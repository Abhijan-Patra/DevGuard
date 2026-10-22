"""One-machine launcher. Owns only its recorded DevGuard process, never Docker/Ollama."""
import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import stat
import subprocess
import sys
import time
import webbrowser
import secrets
from devguard.platform_io import private_directory, private_open, file_lock

import httpx

from devguard.config import MODEL, MODEL_DIGEST
from devguard.runtime import workspace_root
from devguard.bootstrap import ASSETS, RUNNER_TAG, build_runner

ROOT = workspace_root()
RUNTIME = ROOT / '.devguard'
RECORD = RUNTIME / 'local-runtime.json'


def command(args, **kwargs):
    return subprocess.run(args, cwd=ROOT, check=True, **kwargs)


def private_root():
    if ROOT.is_symlink():
        raise RuntimeError('Workspace directory cannot be a symlink')
    ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
    if RUNTIME.is_symlink():
        raise RuntimeError('Runtime directory cannot be a symlink')
    private_directory(RUNTIME)


def private_write(path, value):
    try:
        fd = private_open(path, os.O_WRONLY | os.O_CREAT)
    except OSError:
        raise RuntimeError('Runtime files must be private, regular and owned by this user') from None
    with os.fdopen(fd, 'w', encoding='utf-8', newline='') as stream:
        os.ftruncate(stream.fileno(), 0)
        stream.write(value)


def load_record():
    try:
        fd = private_open(RECORD, os.O_RDONLY)
    except FileNotFoundError:
        return None
    with os.fdopen(fd) as stream:
        info = os.fstat(stream.fileno())
        if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                or (os.name != 'nt' and info.st_mode & 0o077) or info.st_size > 8192):
            raise RuntimeError('Runtime record must be a bounded private regular file')
        data = json.load(stream)
    if (not isinstance(data, dict) or type(data.get('pid')) is not int or data['pid'] <= 1
            or type(data.get('port')) is not int or not 1024 <= data['port'] <= 65535
            or not isinstance(data.get('command'), str) or not isinstance(data.get('process_start'), str)):
        raise RuntimeError('Runtime record is invalid; no process will be stopped')
    return data


def owned(record):
    if not isinstance(record, dict) or type(record.get('pid')) is not int:
        return False
    if os.name == 'nt':
        from devguard.windows import process_identity
        args, created = process_identity(record['pid'])
        return (bool(args) and args == record.get('argv') and created == record.get('process_start')
                and args[1:5] == ['-m', 'devguard', '--port', str(record.get('port'))]
                and bool(__import__('re').fullmatch(r'Local\\DevGuard-[0-9a-f]{64}', record.get('shutdown_event', ''))))
    result = subprocess.run(['ps', '-p', str(record['pid']), '-o', 'command='], capture_output=True, text=True)
    text = result.stdout.strip()
    started = subprocess.run(['ps', '-p', str(record['pid']), '-o', 'lstart='], capture_output=True, text=True).stdout.strip()
    return (result.returncode == 0 and bool(record.get('command')) and bool(record.get('process_start'))
            and text.partition(' -m devguard ')[2] == record['command'].partition(' -m devguard ')[2]
            and started == record['process_start']
            and ' -m devguard --port ' + str(record['port']) + ' ' in text + ' ')


def ready(url):
    try:
        with httpx.Client(trust_env=False, timeout=2) as client:
            return client.get(url).status_code == 200
    except httpx.HTTPError:
        return False


def wait_until(check, seconds, label):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if check():
            return
        time.sleep(1)
    raise RuntimeError(label + ' did not become ready; inspect its application status')


def ensure_dependencies(*, privacy_only=False):
    from devguard.guard.scanner import CredentialScanner
    if not CredentialScanner().available:
        brew = shutil.which('brew')
        if brew is None:
            raise RuntimeError('Install Gitleaks from its official distribution before starting')
        print('Installing the required credential scanner from Homebrew…', flush=True)
        command([brew, 'install', 'gitleaks'])
        if not CredentialScanner().available:
            raise RuntimeError('Credential scanner remains unavailable; startup is held')
    docker = shutil.which('docker')
    ollama = shutil.which('ollama')
    if not ollama:
        raise RuntimeError('Install official Ollama first: https://ollama.com/download')
    if not docker and not privacy_only:
        raise RuntimeError('Install Docker Desktop for repairs, or use --privacy-only')
    def docker_ready():
        return subprocess.run([docker, 'info'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10).returncode == 0
    if not privacy_only and not docker_ready():
        if sys.platform != 'darwin':
            raise RuntimeError('Start the Docker engine first, then retry')
        print('Starting Docker Desktop…', flush=True)
        command(['open', '-a', 'Docker'])
        wait_until(docker_ready, 120, 'Docker')
    if not ready('http://127.0.0.1:11434/api/version'):
        if sys.platform != 'darwin':
            raise RuntimeError('Start Ollama (ollama serve), then retry')
        print('Starting Ollama…', flush=True)
        command(['open', '-a', 'Ollama'])
        wait_until(lambda: ready('http://127.0.0.1:11434/api/version'), 60, 'Ollama')
    with httpx.Client(trust_env=False, timeout=5) as client:
        models = client.get('http://127.0.0.1:11434/api/tags').json()['models']
    selected = next((model for model in models if model['name'] == MODEL), None)
    if selected is None:
        if os.name == 'nt':
            from devguard.windows import exact_pull_active
            active = exact_pull_active(MODEL)
        else:
            processes = command(['ps', '-Ao', 'command='], capture_output=True, text=True).stdout
            active = any(('ollama pull ' + MODEL in line or 'ollama run ' + MODEL in line) for line in processes.splitlines())
        if active:
            raise RuntimeError('The exact Gemma download is already active; let it finish, then start again')
        print('Downloading the exact pinned Gemma package…', flush=True)
        command([ollama, 'pull', MODEL])
        with httpx.Client(trust_env=False, timeout=5) as client:
            selected = next((m for m in client.get('http://127.0.0.1:11434/api/tags').json()['models'] if m['name'] == MODEL), None)
    if selected is None or selected.get('digest') != MODEL_DIGEST:
        raise RuntimeError('Gemma digest mismatch. No substitute model will be used')
    if privacy_only:
        return None
    inspected = subprocess.run([docker, 'image', 'inspect', RUNNER_TAG, '--format', '{{.Id}}'], capture_output=True, text=True)
    if inspected.returncode != 0:
        print('Building the restricted verifier with a minimal public build context…', flush=True)
        build_runner(docker)
        inspected = command([docker, 'image', 'inspect', RUNNER_TAG, '--format', '{{.Id}}'], capture_output=True, text=True)
    return inspected.stdout.strip()


def demo_manifest(image_id):
    directory = RUNTIME / 'local-demo'
    if directory.is_symlink():
        raise RuntimeError('Demo directory cannot be a symlink')
    private_directory(directory)
    for name in ('cart.py', 'main.py'):
        target = directory / name
        if target.is_symlink():
            raise RuntimeError('Demo source cannot be a symlink')
        if not target.exists():
            private_write(target, (ASSETS / 'demo' / name).read_text())
    config = {'projects': [{'project_id': 'demo-cart', 'root': str(directory),
                            'source_files': ['cart.py', 'main.py'], 'writable_files': ['cart.py'],
                            'trusted_tests': str(ASSETS / 'checks'), 'test_names': ['cart'], 'image_id': image_id}]}
    path = RUNTIME / 'local-projects.json'
    private_write(path, json.dumps(config, indent=2))
    return path


def start(args):
    private_root()
    record = load_record()
    if owned(record):
        print('DevGuard is already running: http://127.0.0.1:%s/app' % record['port'])
        return
    with socket.socket() as probe:
        try:
            probe.bind(('127.0.0.1', args.port))
        except OSError:
            raise RuntimeError('A service already owns this port. It will not be replaced') from None
    config = args.projects_config
    if config:
        from devguard.repair.projects import load_projects
        load_projects(config)
    image = ensure_dependencies(privacy_only=args.privacy_only)
    config = config or (demo_manifest(image) if image else None)
    log_path = RUNTIME / 'local-server.log'
    fd = private_open(log_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND)
    shutdown_event = 'Local\\DevGuard-' + secrets.token_hex(32) if os.name == 'nt' else None
    with os.fdopen(fd, 'a', encoding='utf-8') as log:
        argv = [sys.executable, '-m', 'devguard', '--port', str(args.port)]
        if config:
            argv += ['--projects-config', str(config)]
        env = os.environ.copy()
        if shutdown_event:
            env['DEVGUARD_SHUTDOWN_EVENT'] = shutdown_event
        options = {'creationflags': subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == 'nt' else {'start_new_session': True}
        process = subprocess.Popen(argv, cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                                   stdout=log, stderr=log, **options)
    if os.name == 'nt':
        from devguard.windows import process_identity
        actual, process_start = process_identity(process.pid)
        expected_command = subprocess.list2cmdline(actual)
    else:
        expected_command = ''
        for _ in range(20):
            expected_command = subprocess.run(['ps', '-p', str(process.pid), '-o', 'command='], capture_output=True, text=True).stdout.strip()
            if ' -m devguard --port ' in expected_command:
                break
            time.sleep(.05)
        process_start = subprocess.run(['ps', '-p', str(process.pid), '-o', 'lstart='], capture_output=True, text=True).stdout.strip()
    private_write(RECORD, json.dumps({'pid': process.pid, 'port': args.port, 'started_at': time.time(),
        'command': expected_command, 'process_start': process_start, 'argv': argv, 'shutdown_event': shutdown_event}))
    wait_until(lambda: ready('http://127.0.0.1:%s/health' % args.port), 45, 'DevGuard')
    url = 'http://127.0.0.1:%s/app' % args.port
    print('Ready: ' + url)
    print('Clipboard OFF · file watchers OFF · repair ' + ('PAUSED' if config else 'NOT CONFIGURED') + '.')
    if not args.no_open:
        webbrowser.open(url)


def stop():
    record = load_record()
    if not owned(record):
        print('No owned DevGuard backend is running. Docker and Ollama are untouched.')
        return
    if os.name == 'nt':
        from devguard.windows import signal_shutdown
        signal_shutdown(record['shutdown_event'])
    else:
        os.kill(record['pid'], signal.SIGTERM)
    wait_until(lambda: not owned(record), 75, 'DevGuard shutdown')
    RECORD.unlink(missing_ok=True)
    print('DevGuard stopped gracefully. Docker and Ollama are untouched.')


def main(argv=None):
    parser = argparse.ArgumentParser(description='DevGuard single-laptop launcher')
    parser.add_argument('action', choices=['start', 'status', 'stop', 'doctor'])
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--no-open', action='store_true')
    parser.add_argument('--projects-config', type=Path)
    parser.add_argument('--privacy-only', action='store_true', help='Run context/clipboard without Docker or repair registration')
    parser.add_argument('--json', action='store_true', help='Machine-readable doctor output')
    args = parser.parse_args(argv)
    if not 1024 <= args.port <= 65535:
        parser.error('Choose a port between 1024 and 65535')
    if args.privacy_only and args.projects_config:
        parser.error('--privacy-only cannot register repair projects')
    try:
        if args.action == 'doctor':
            from devguard.doctor import diagnose
            report = diagnose(privacy_only=args.privacy_only)
            if args.json:
                print(json.dumps(report))
            else:
                print('DevGuard prerequisites (no clipboard reads or inference):')
                for check in report['checks']:
                    print(('OK  ' if check['ready'] else 'FIX ' if check['required'] else 'INFO') + ' ' + check['name'])
                    if check['action']:
                        print('     ' + check['action'])
                print('Ready.' if report['ready'] else 'Complete the required FIX items, then retry.')
            return 0 if report['ready'] else 1
        if sys.platform not in {'darwin', 'linux', 'win32'}:
            raise RuntimeError('The managed launcher supports macOS, Windows and Linux')
        if args.projects_config:
            args.projects_config = args.projects_config.expanduser().resolve(strict=True)
        private_root()
        lock_path = RUNTIME / 'launcher.lock'
        try:
            lock_context = file_lock(lock_path)
            lock_context.__enter__()
        except BlockingIOError:
            raise RuntimeError('Another launcher operation is active; do not start a duplicate') from None
        try:
            # The detached server cannot inherit this descriptor.
            if args.action == 'start':
                start(args)
            elif args.action == 'stop':
                stop()
            else:
                record = load_record()
                print(json.dumps({'running': owned(record), 'port': record['port'] if record else None,
                                  'healthy': ready('http://127.0.0.1:%s/health' % record['port']) if record else False}))
        finally:
            lock_context.__exit__(None, None, None)
    except (RuntimeError, OSError, subprocess.SubprocessError, ValueError, httpx.HTTPError) as error:
        # Only launcher-controlled messages; no model input is handled here.
        print('Startup held: ' + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
