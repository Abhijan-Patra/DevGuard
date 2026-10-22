"""Real Windows APIs against disposable synthetic data. No model accuracy claim."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

pytestmark = pytest.mark.skipif(os.name != 'nt', reason='Requires native Windows handles/ACLs')


def private_root(tmp_path):
    from devguard.platform_io import private_directory
    root = tmp_path / 'private workspace with spaces'
    private_directory(root)
    return root


def test_private_acl_token_hardlink_and_public_directory_rejection(tmp_path):
    import win32security, ntsecuritycon
    from devguard.platform_io import private_open, private_directory
    from devguard.client import private_token
    root = private_root(tmp_path)
    path = root / 'token'
    with os.fdopen(private_open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY), 'w') as f:
        f.write('synthetic-only-private-token-924017563890')
    assert private_token(path).startswith('synthetic-only')
    os.link(path, root / 'alias')
    with pytest.raises(OSError):private_token(path)
    (root / 'alias').unlink()
    sd = win32security.GetNamedSecurityInfo(str(root), win32security.SE_FILE_OBJECT, win32security.DACL_SECURITY_INFORMATION)
    acl = sd.GetSecurityDescriptorDacl()
    acl.AddAccessAllowedAce(win32security.ACL_REVISION, ntsecuritycon.FILE_ALL_ACCESS,
        win32security.CreateWellKnownSid(win32security.WinWorldSid))
    win32security.SetNamedSecurityInfo(str(root), win32security.SE_FILE_OBJECT,
        win32security.DACL_SECURITY_INFORMATION | win32security.PROTECTED_DACL_SECURITY_INFORMATION,
        None, None, acl, None)
    with pytest.raises(OSError):private_directory(root)


def test_source_reads_apply_rollback_and_hardlink_refusal(tmp_path):
    from devguard.repair.workspace import read_source, atomic_replace_source
    from devguard.repair.contracts import RepairError
    root = tmp_path / 'project';root.mkdir()
    path = root / 'cart.py';path.write_bytes(b'VALUE = 1\r\n')
    original = read_source(root, 'cart.py')
    atomic_replace_source(root, 'cart.py', b'VALUE = 2\n', {'cart.py': original})
    assert path.read_bytes() == b'VALUE = 2\n'
    with pytest.raises(RepairError):
        atomic_replace_source(root, 'cart.py', b'VALUE = 3\n', {'cart.py': original})
    assert path.read_bytes() == b'VALUE = 2\n'
    atomic_replace_source(root, 'cart.py', original, {'cart.py': b'VALUE = 2\n'})
    assert path.read_bytes() == original
    os.link(path, root / 'alias.py')
    with pytest.raises(RepairError):read_source(root, 'cart.py')


def test_junction_parent_escape_and_locked_root_replacement_are_refused(tmp_path):
    from devguard.guard.paths import ProjectFiles
    from devguard.guard.engine import GuardError
    root = tmp_path / 'project';root.mkdir()
    outside = tmp_path / 'outside';outside.mkdir()
    (outside / 'source.py').write_text('OUTSIDE = True\n')
    (root / 'source.py').write_text('INSIDE = True\n')
    junction = root / 'jump'
    subprocess.run(['cmd', '/c', 'mklink', '/J', str(junction), str(outside)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    files = ProjectFiles(root)
    try:
        assert files.read_text('source.py') == 'INSIDE = True\n'
        with pytest.raises(GuardError):files.read_text('jump/source.py')
        with pytest.raises(OSError):root.rename(tmp_path / 'moved')
    finally:
        files.close();junction.rmdir()


def test_launcher_lock_excludes_another_process(tmp_path):
    from devguard.platform_io import file_lock
    root = private_root(tmp_path)
    path = root / 'launcher.lock'
    code = 'from devguard.platform_io import file_lock\nimport sys\nwith file_lock(sys.argv[1]): pass'
    with file_lock(path):
        child = subprocess.run([sys.executable, '-c', code, str(path)], capture_output=True)
        assert child.returncode != 0
    assert subprocess.run([sys.executable, '-c', code, str(path)], capture_output=True).returncode == 0


def test_process_ownership_and_private_event_graceful_stop(tmp_path, monkeypatch):
    import secrets
    from devguard import local
    from devguard.windows import process_identity, signal_shutdown
    event = 'Local\\DevGuard-' + secrets.token_hex(32)
    code = ('import time\nfrom types import SimpleNamespace\nfrom devguard.windows import graceful_server\n'
            's=SimpleNamespace(should_exit=False)\nwith graceful_server(s, __import__("sys").argv[1]):\n'
            ' print("READY",flush=True)\n while not s.should_exit: time.sleep(.05)\nprint("STOPPED",flush=True)')
    child = subprocess.Popen([sys.executable, '-u', '-c', code, event], stdout=subprocess.PIPE, text=True)
    try:
        assert child.stdout.readline().strip() == 'READY'
        args, started = process_identity(child.pid)
        assert args and started
        assert process_identity(2147483647) == ([], '')
        # Identity for an unrelated process can never pass the DevGuard argv check.
        assert not local.owned({'pid':child.pid, 'port':8765,'argv':args,
            'process_start':started,'shutdown_event':event})
        signal_shutdown(event)
        assert child.communicate(timeout=10)[0].strip() == 'STOPPED'
        assert child.returncode == 0
    finally:
        if child.poll() is None:child.kill();child.wait()


@pytest.mark.skipif(os.environ.get('DEVGUARD_WINDOWS_CLIPBOARD_TEST') != '1',
    reason='Explicit opt-in only on a disposable Windows CI desktop; never touch developer clipboard')
def test_unicode_clipboard_stale_copy_non_text_and_bounded_reads():
    import win32clipboard
    from devguard.clipboard.native import WindowsClipboard
    adapter = WindowsClipboard()
    # This hosted CI worker has no personal clipboard; declare all bytes synthetic.
    initial = adapter.counter()
    first = adapter.write_text(initial, 'Synthetic α café 😀\r\nsecond line')
    assert first is not None
    assert adapter.read_text(4096) == ('TEXT','Synthetic α café 😀\r\nsecond line')
    assert adapter.read_text(1)[0] == 'OVERSIZE'
    second = adapter.write_text(first, 'Synthetic newer copy')
    assert second is not None and second != first
    assert adapter.write_text(first, 'Must not replace newer copy') is None
    assert adapter.read_text(4096) == ('TEXT','Synthetic newer copy')
    assert adapter.write_text(second, 'A\0B') is None
    # Empty (no Unicode format) is skipped, never decoded as private text.
    win32clipboard.OpenClipboard()
    try:win32clipboard.EmptyClipboard()
    finally:win32clipboard.CloseClipboard()
    assert adapter.read_text(4096) == ('NON_TEXT',None)


def test_managed_backend_start_status_duplicate_refusal_and_graceful_stop(tmp_path):
    """Actual backend/lifecycle; external dependency check is a declared double."""
    import socket
    env = os.environ.copy()
    env['DEVGUARD_HOME'] = str(tmp_path / 'disposable installed home')
    for key in ('DEVGUARD_SESSION_TOKEN','DEVGUARD_ADAPTER_TOKEN','DEVGUARD_SHUTDOWN_EVENT'):
        env.pop(key, None)
    with socket.socket() as probe:
        probe.bind(('127.0.0.1',0));port = probe.getsockname()[1]
    code = ('from devguard import local\nlocal.ensure_dependencies=lambda **kw: None\n'
            f'raise SystemExit(local.main(["start","--privacy-only","--no-open","--port","{port}"]))')
    def run(args):
        return subprocess.run([sys.executable, *args], env=env, capture_output=True, text=True, timeout=90, check=True)
    try:
        started = run(['-c',code])
        assert 'Ready:' in started.stdout
        state = json.loads(run(['-m','devguard','status']).stdout)
        assert state['running'] and state['healthy'] and state['port'] == port
        assert 'already running' in run(['-c',code]).stdout
        assert 'stopped gracefully' in run(['-m','devguard','stop']).stdout
        assert json.loads(run(['-m','devguard','status']).stdout)['running'] is False
    finally:
        subprocess.run([sys.executable,'-m','devguard','stop'],env=env,capture_output=True,timeout=90)
