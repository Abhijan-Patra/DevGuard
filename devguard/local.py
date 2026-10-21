"""One-machine launcher. Owns only its recorded DevGuard process, never Docker/Ollama."""
import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import webbrowser

import httpx

from devguard.config import MODEL, MODEL_DIGEST

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / '.devguard'
RECORD = RUNTIME / 'local-runtime.json'


def command(args, **kwargs):
    return subprocess.run(args, cwd=ROOT, check=True, **kwargs)


def private_root():
    if RUNTIME.is_symlink():
        raise RuntimeError('Runtime directory cannot be a symlink')
    RUNTIME.mkdir(mode=0o700, exist_ok=True)
    if RUNTIME.stat().st_mode & 0o077:
        raise RuntimeError('Runtime directory must be private (mode 0700)')


def private_write(path, value):
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, 'O_NOFOLLOW', 0)
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, 'w') as stream:
        stream.write(value)


def load_record():
    if RECORD.is_symlink():
        raise RuntimeError('Runtime record cannot be a symlink')
    try:
        return json.loads(RECORD.read_text())
    except FileNotFoundError:
        return None


def owned(record):
    if not record or type(record.get('pid')) is not int:
        return False
    result = subprocess.run(['ps', '-p', str(record['pid']), '-o', 'command='], capture_output=True, text=True)
    text = result.stdout.strip()
    started = subprocess.run(['ps', '-p', str(record['pid']), '-o', 'lstart='], capture_output=True, text=True).stdout.strip()
    return (result.returncode == 0 and bool(record.get('command')) and bool(record.get('process_start'))
            and text.partition(' -m devguard ')[2] == record['command'].partition(' -m devguard ')[2]
            and started == record['process_start']
            and ' -m devguard --port ' + str(record['port']) + ' ' in text)


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


def ensure_dependencies():
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
    if not docker or not ollama:
        raise RuntimeError('Install official Docker Desktop and Ollama applications first')
    def docker_ready():
        return subprocess.run([docker, 'info'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10).returncode == 0
    if not docker_ready():
        print('Starting Docker Desktop…', flush=True)
        command(['open', '-a', 'Docker'])
        wait_until(docker_ready, 120, 'Docker')
    if not ready('http://127.0.0.1:11434/api/version'):
        print('Starting Ollama…', flush=True)
        command(['open', '-a', 'Ollama'])
        wait_until(lambda: ready('http://127.0.0.1:11434/api/version'), 60, 'Ollama')
    with httpx.Client(trust_env=False, timeout=5) as client:
        models = client.get('http://127.0.0.1:11434/api/tags').json()['models']
    selected = next((model for model in models if model['name'] == MODEL), None)
    if selected is None:
        processes = command(['ps', '-Ao', 'command='], capture_output=True, text=True).stdout
        if any(('ollama pull ' + MODEL in line or 'ollama run ' + MODEL in line) for line in processes.splitlines()):
            raise RuntimeError('The exact Gemma download is already active; let it finish, then start again')
        print('Downloading the exact pinned Gemma package…', flush=True)
        command([ollama, 'pull', MODEL])
        with httpx.Client(trust_env=False, timeout=5) as client:
            selected = next((m for m in client.get('http://127.0.0.1:11434/api/tags').json()['models'] if m['name'] == MODEL), None)
    if selected is None or selected.get('digest') != MODEL_DIGEST:
        raise RuntimeError('Gemma digest mismatch. No substitute model will be used')
    inspected = subprocess.run([docker, 'image', 'inspect', 'devguard-runner:mac2', '--format', '{{.Id}}'], capture_output=True, text=True)
    if inspected.returncode != 0:
        print('Building the restricted verifier with a minimal public build context…', flush=True)
        command([sys.executable, 'demo/backend/build_runner.py'])
        inspected = command([docker, 'image', 'inspect', 'devguard-runner:mac2', '--format', '{{.Id}}'], capture_output=True, text=True)
    return inspected.stdout.strip()


def demo_manifest(image_id):
    directory = RUNTIME / 'local-demo'
    if directory.is_symlink():
        raise RuntimeError('Demo directory cannot be a symlink')
    directory.mkdir(mode=0o700, exist_ok=True)
    for name in ('cart.py', 'main.py'):
        target = directory / name
        if not target.exists():
            private_write(target, (ROOT / 'demo' / 'backend' / name).read_text())
        elif target.is_symlink():
            raise RuntimeError('Demo source cannot be a symlink')
    config = {'projects': [{'project_id': 'demo-cart', 'root': str(directory),
                            'source_files': ['cart.py', 'main.py'], 'writable_files': ['cart.py'],
                            'trusted_tests': str(ROOT / 'trusted_tests'), 'test_names': ['cart'], 'image_id': image_id}]}
    path = RUNTIME / 'local-projects.json'
    private_write(path, json.dumps(config, indent=2))
    return path


def start(args):
    private_root()
    record = load_record()
    if owned(record):
        print('DevGuard is already running: http://127.0.0.1:%s/app' % record['port'])
        return
    if ready('http://127.0.0.1:%s/health' % args.port):
        raise RuntimeError('A service already owns this port. It will not be replaced')
    image = ensure_dependencies()
    config = args.projects_config or demo_manifest(image)
    log_path = RUNTIME / 'local-server.log'
    fd = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    with os.fdopen(fd, 'a') as log:
        process = subprocess.Popen([sys.executable, '-m', 'devguard', '--port', str(args.port), '--projects-config', str(config)],
                                   cwd=ROOT, stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
    expected_command = ''
    for _ in range(20):
        expected_command = subprocess.run(['ps', '-p', str(process.pid), '-o', 'command='], capture_output=True, text=True).stdout.strip()
        if ' -m devguard --port ' in expected_command:
            break
        time.sleep(.05)
    process_start = subprocess.run(['ps', '-p', str(process.pid), '-o', 'lstart='], capture_output=True, text=True).stdout.strip()
    private_write(RECORD, json.dumps({'pid': process.pid, 'port': args.port, 'started_at': time.time(),
                                    'command': expected_command, 'process_start': process_start}))
    wait_until(lambda: ready('http://127.0.0.1:%s/health' % args.port), 45, 'DevGuard')
    url = 'http://127.0.0.1:%s/app' % args.port
    print('Ready: ' + url)
    print('Clipboard OFF · file watchers OFF · repair PAUSED. Demo source is a disposable local copy.')
    if not args.no_open:
        webbrowser.open(url)


def stop():
    record = load_record()
    if not owned(record):
        print('No owned DevGuard backend is running. Docker and Ollama are untouched.')
        return
    os.kill(record['pid'], signal.SIGTERM)
    wait_until(lambda: not owned(record), 75, 'DevGuard shutdown')
    RECORD.unlink(missing_ok=True)
    print('DevGuard stopped gracefully. Docker and Ollama are untouched.')


def main():
    parser = argparse.ArgumentParser(description='DevGuard single-laptop launcher')
    parser.add_argument('action', choices=['start', 'status', 'stop'])
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--no-open', action='store_true')
    parser.add_argument('--projects-config', type=Path)
    args = parser.parse_args()
    try:
        if args.action == 'start':
            start(args)
        elif args.action == 'stop':
            stop()
        else:
            record = load_record()
            print(json.dumps({'running': owned(record), 'port': record['port'] if record else None,
                              'healthy': ready('http://127.0.0.1:%s/health' % record['port']) if record else False}))
    except (RuntimeError, OSError, subprocess.SubprocessError, ValueError) as error:
        # Only launcher-controlled messages; no model input is handled here.
        print('Startup held: ' + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
