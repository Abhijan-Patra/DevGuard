"""Install/lifecycle safety with isolated directories and declared dependency doubles."""
import io
import json
import os
from pathlib import Path
import socket
import tarfile
from types import SimpleNamespace

import httpx
import pytest

from devguard import local
from devguard.bootstrap import ASSETS, build_context
from devguard.config import MODEL, MODEL_DIGEST
from devguard.doctor import diagnose
from devguard.repair.projects import load_projects
from devguard.runtime import workspace_root


def private_workspace(monkeypatch, tmp_path):
    root = tmp_path.resolve() / 'installed-workspace'
    monkeypatch.setattr(local, 'ROOT', root)
    monkeypatch.setattr(local, 'RUNTIME', root / '.devguard')
    monkeypatch.setattr(local, 'RECORD', root / '.devguard/local-runtime.json')
    local.private_root()
    return root


def test_workspace_override_is_canonical_and_does_not_depend_on_cwd(monkeypatch, tmp_path):
    root = tmp_path.resolve() / 'isolated'
    monkeypatch.setenv('DEVGUARD_HOME', str(root))
    monkeypatch.chdir(tmp_path)
    assert workspace_root() == root
    root.mkdir()
    link = tmp_path / 'linked';link.symlink_to(root, target_is_directory=True)
    monkeypatch.setenv('DEVGUARD_HOME', str(link))
    with pytest.raises(ValueError, match='canonical'):
        workspace_root()


def test_packaged_demo_and_independent_oracle_match_reviewed_sources():
    source = Path(__file__).resolve().parents[2]
    for name in ('cart.py', 'main.py', 'Dockerfile'):
        assert (ASSETS / 'demo' / name).read_bytes() == (source / 'demo/backend' / name).read_bytes()
    assert (ASSETS / 'demo/requirements-dev.lock').read_bytes() == (source / 'tests/backend/requirements-dev.lock').read_bytes()
    assert (ASSETS / 'checks/test_cart.py').read_bytes() == (source / 'trusted_tests/test_cart.py').read_bytes()
    with tarfile.open(fileobj=io.BytesIO(build_context())) as archive:
        assert archive.getnames() == ['Dockerfile', 'tests/backend/requirements-dev.lock']
        assert all(m.uid == 0 and not m.uname and m.isfile() for m in archive)


def test_installed_demo_is_disposable_and_preserves_existing_user_edits(monkeypatch, tmp_path):
    root = private_workspace(monkeypatch, tmp_path)
    manifest = local.demo_manifest('sha256:' + 'a' * 64)
    spec, = load_projects(manifest)
    assert spec.root == root / '.devguard/local-demo'
    assert spec.trusted_tests == root / '.devguard/local-demo-checks'
    assert (spec.trusted_tests/'test_cart.py').read_bytes() == (ASSETS/'checks/test_cart.py').read_bytes()
    edited = spec.root / 'cart.py'
    edited.write_text('USER_EDIT = True\n')
    local.demo_manifest('sha256:' + 'b' * 64)
    assert edited.read_text() == 'USER_EDIT = True\n'
    edited.unlink();edited.symlink_to(tmp_path / 'other.py')
    with pytest.raises(RuntimeError, match='symlink'):
        local.demo_manifest('sha256:' + 'a' * 64)


def test_private_write_rejects_links_before_truncating_another_file(monkeypatch, tmp_path):
    root = private_workspace(monkeypatch, tmp_path)
    original = tmp_path / 'preserve';original.write_text('synthetic private marker');original.chmod(0o600)
    linked = root / '.devguard/linked';os.link(original, linked)
    with pytest.raises(RuntimeError, match='private, regular'):
        local.private_write(linked, 'overwrite')
    assert original.read_text() == 'synthetic private marker'


def test_concurrent_launch_is_rejected_before_setup(monkeypatch, tmp_path, capsys):
    private_workspace(monkeypatch, tmp_path)
    calls = []
    def start(args):
        calls.append(True)
        assert local.main(['start', '--privacy-only', '--no-open']) == 1
    monkeypatch.setattr(local, 'start', start)
    assert local.main(['start', '--privacy-only', '--no-open']) == 0
    assert len(calls) == 1
    assert 'Another launcher operation is active' in capsys.readouterr().err


def test_occupied_port_never_runs_setup_or_replaces_service(monkeypatch, tmp_path):
    private_workspace(monkeypatch, tmp_path)
    monkeypatch.setattr(local, 'ensure_dependencies', lambda **kw: pytest.fail('must check port before setup'))
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0));listener.listen()
        with pytest.raises(RuntimeError, match='already owns this port'):
            local.start(SimpleNamespace(port=listener.getsockname()[1], privacy_only=True, projects_config=None, no_open=True))


def test_doctor_is_read_only_and_checks_exact_model_digest(monkeypatch):
    import devguard.guard.scanner
    monkeypatch.setattr(devguard.guard.scanner, 'CredentialScanner', lambda: SimpleNamespace(available=True))
    def transport(request):
        assert request.method == 'GET' and request.url.path in {'/api/version', '/api/tags'}
        return httpx.Response(200, json={'version': 'test-runtime'} if request.url.path == '/api/version' else
                              {'models': [{'name': MODEL, 'digest': MODEL_DIGEST}]})
    report = diagnose(privacy_only=True, transport=httpx.MockTransport(transport))
    assert report['ready'] and not report['clipboard_read'] and not report['inference_sent']
    missing = diagnose(privacy_only=True, transport=httpx.MockTransport(lambda r: httpx.Response(200, json={'models': []})))
    assert not missing['ready']
    assert any(c['name'] == 'pinned_model' and not c['ready'] for c in missing['checks'])


def test_foreground_demo_factory_uses_bundled_disposable_source_without_checkout_imports(monkeypatch, tmp_path):
    from devguard.api.repair_integration import demo_repair_factory
    root = private_workspace(monkeypatch, tmp_path)
    factory = demo_repair_factory(root, 'sha256:' + 'a' * 64)
    assert callable(factory)
    spec, = load_projects(root / '.devguard/local-projects.json')
    assert spec.root == root / '.devguard/local-demo'
    assert spec.trusted_tests == root / '.devguard/local-demo-checks'
    assert (spec.trusted_tests/'test_cart.py').read_bytes() == (ASSETS/'checks/test_cart.py').read_bytes()
    assert (spec.root / 'cart.py').read_bytes() == (ASSETS / 'demo/cart.py').read_bytes()


def test_release_failure_report_preserves_dependency_hold_without_exception_payload(tmp_path):
    from scripts.release_smoke import capture_report
    output = tmp_path / 'failed-trial.json'
    report = {'repair_state': 'BLOCKED', 'repair_reason': 'BASELINE_UNAVAILABLE', 'checks': {}}
    with pytest.raises(RuntimeError):
        with capture_report(report, output):
            raise RuntimeError('synthetic-private-exception-detail')
    data = json.loads(output.read_text())
    assert data['passed'] is False and data['repair_reason'] == 'BASELINE_UNAVAILABLE'
    assert 'synthetic-private-exception-detail' not in output.read_text()


def test_startup_warmup_never_sends_private_input_or_uses_an_unpinned_model():
    requests = []
    def respond(request):
        requests.append(request)
        if request.method == 'GET':
            return httpx.Response(200, json={'models':[{'name':MODEL,'digest':MODEL_DIGEST}]})
        body = json.loads(request.content)
        assert request.url.path == '/api/generate'
        assert body == {'model':MODEL,'stream':False,'keep_alive':'5m','options':{'num_ctx':4096}}
        assert 'prompt' not in body and 'messages' not in body
        return httpx.Response(200, json={'done':True})
    local.warm_model(transport=httpx.MockTransport(respond))
    assert [r.method for r in requests] == ['GET','POST']
    def mismatch(request):
        assert request.method == 'GET'
        return httpx.Response(200, json={'models':[{'name':MODEL,'digest':'wrong'}]})
    with pytest.raises(RuntimeError, match='digest mismatch'):
        local.warm_model(transport=httpx.MockTransport(mismatch))


def test_default_oracle_copy_is_independent_and_edited_copy_holds_without_overwrite(monkeypatch, tmp_path):
    root = private_workspace(monkeypatch, tmp_path)
    manifest = local.demo_manifest('sha256:' + 'a' * 64)
    spec, = load_projects(manifest)
    assert not spec.trusted_tests.is_relative_to(spec.root)
    oracle = spec.trusted_tests/'test_cart.py'
    original = (ASSETS/'checks/test_cart.py').read_bytes()
    assert oracle.read_bytes() == original
    oracle.write_bytes(b'# declared synthetic operator edit\n')
    with pytest.raises(RuntimeError, match='Independent demo checks changed'):
        local.demo_manifest('sha256:' + 'a' * 64)
    assert oracle.read_bytes() == b'# declared synthetic operator edit\n'
    assert (ASSETS/'checks/test_cart.py').read_bytes() == original
    oracle.write_bytes(original)
    (spec.trusted_tests/'unexpected.txt').write_text('declared synthetic extra file')
    with pytest.raises(RuntimeError, match='unexpected files'):
        local.demo_manifest('sha256:' + 'a' * 64)
    assert oracle.read_bytes() == original
