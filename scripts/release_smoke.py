"""Run with the wheel's clean virtualenv, outside the checkout. Synthetic data only.

Default: foreground API/assets and held/approved privacy contract, no downloads.
--live: normal managed startup, real Gemma/Gitleaks, Docker repair/apply/rollback.
Neither mode enables clipboard observation or changes an existing user's workspace.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time

import httpx


@contextmanager
def capture_report(report, output):
    try:
        yield
    except BaseException as error:
        report['passed'] = False
        # No exception message: it may include private paths or transport data.
        report['failure_type'] = type(error).__name__
        raise
    else:
        report['passed'] = True
    finally:
        if output:
            output.write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    from devguard.bootstrap import ASSETS
    package = Path(__import__('devguard').__file__).resolve()
    assert 'site-packages' in str(package), 'This check must run against the installed wheel, not an editable checkout'
    with tempfile.TemporaryDirectory(prefix='devguard-release-') as temporary:
        root = Path(temporary).resolve()
        workspace = root / 'private-home'
        env = {k: v for k, v in os.environ.items() if k not in {'PYTHONPATH', 'DEVGUARD_SESSION_TOKEN', 'DEVGUARD_ADAPTER_TOKEN', 'DEVGUARD_OLLAMA_URL', 'DEVGUARD_MODEL'}}
        env['DEVGUARD_HOME'] = str(workspace)
        if os.name == 'nt':
            import secrets
            env['DEVGUARD_SHUTDOWN_EVENT'] = 'Local\\DevGuard-' + secrets.token_hex(32)
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', 0));port = probe.getsockname()[1]
        base = f'http://127.0.0.1:{port}'
        prefix = [sys.executable, '-I', '-m', 'devguard']
        process = None
        report = {'timestamp': datetime.now(timezone.utc).isoformat(),
                  'scope': 'Clean installed wheel; temporary private workspace; declared synthetic input',
                  'live_model_and_docker': args.live, 'clipboard_enabled': False, 'checks': {},
                  'general_clipboard_accessed': False,
                  'installed_version': __import__('importlib.metadata', fromlist=['version']).version('devguard')}
        oracle_hash = hashlib.sha256((ASSETS / 'checks/test_cart.py').read_bytes()).hexdigest()
        with capture_report(report, args.output), (root / 'server.log').open('w') as log:
            try:
                argv = prefix + (['start', '--port', str(port), '--no-open'] if args.live else ['serve', '--port', str(port)])
                process = subprocess.Popen(argv, cwd=root, env=env, stdout=log, stderr=log)
                with httpx.Client(base_url=base, timeout=35, trust_env=False, follow_redirects=False) as client:
                    deadline = time.monotonic() + 120
                    while True:
                        try:
                            health = client.get('/health')
                            if health.status_code == 200:break
                        except httpx.HTTPError:pass
                        if time.monotonic() >= deadline or process.poll() not in {None, 0}:
                            raise RuntimeError('Clean installed API did not start; inspect only the temporary local server log')
                        time.sleep(.2)
                    assert client.get('/app').status_code == 200
                    assert 'display_preview' in client.get('/assets/workspace.js').text
                    assert client.get('/api/v1/status').status_code == 401
                    headers = {'Origin': base, 'X-DevGuard-Workspace': '1'}
                    pairing = client.post('/api/v1/session/connect', headers=headers)
                    pairing.raise_for_status()
                    assert 'HttpOnly' in pairing.headers['set-cookie']
                    def api(method, path, body=None):
                        result = client.request(method, '/api/v1' + path, headers=headers, json=body)
                        result.raise_for_status();return result.json()
                    status = api('GET', '/status')
                    assert status['clipboard']['state'] == 'OFF'
                    assert status['clipboard']['safe_preview'] is None
                    assert not status['monitoring']['automatic']
                    report['checks'].update(api_and_assets=True, unauthenticated_access_denied=True,
                        browser_pairing=True, capture_and_watchers_off=True)
                    profile = subprocess.run([sys.executable, '-I', '-m', 'devguard.client_config',
                        '--output', str(workspace / 'synthetic-client-profile'),
                        '--token-file', str(workspace / '.devguard/client-token'),
                        '--base-url', base + '/api/v1'], cwd=root, env=env,
                        capture_output=True, text=True, timeout=15, check=True)
                    profile_result = json.loads(profile.stdout)
                    assert profile_result['global_configuration_changed'] is False
                    assert profile_result['hooks_trusted'] is False
                    report['checks']['isolated_client_profile_without_global_changes'] = True
                    synthetic = 'Debug login: password=synthetic-release-credential-437295; ValueError at auth.py:42'
                    result = api('POST', '/guard/evaluate', {'surface': 'explicit_prompt', 'destination_id': 'local-composer',
                        'content_version': 1, 'task': None, 'text': synthetic})
                    report['privacy'] = {key: result.get(key) for key in ('decision', 'status', 'reason_codes')}
                    assert 'synthetic-release-credential' not in json.dumps(result)
                    if args.live:
                        assert health.json()['model_ready']
                        assert result['decision'] == 'SANITIZE' and result['status'] == 'READY'
                        assert '[CREDENTIAL_' in result['safe_preview']
                        receipt = api('POST', '/guard/requests/' + result['request_id'] + '/deliver',
                                      {'content_version': 1, 'destination_id': 'local-composer'})
                        assert receipt['delivered']
                        assert api('GET', '/composer')['text'] == result['safe_preview']
                        api('DELETE', '/composer')
                        report['checks']['real_sanitized_delivery'] = True
                        assert status['repair']['available'] and status['repair']['state'] == 'PAUSED'
                        projects = api('GET', '/projects')['projects']
                        assert len(projects) == 1 and projects[0]['project_id'] == 'demo-cart'
                        cart = workspace / '.devguard/local-demo/cart.py'
                        original = cart.read_bytes()
                        incident = api('POST', '/incidents', {'project_id': 'demo-cart', 'signal': 'cart'})
                        run = api('POST', '/incidents/' + incident['incident_id'] + '/investigate', {})
                        api('POST', '/scheduler/enter-idle', {})
                        deadline = time.monotonic() + 240
                        while run['state'] not in {'READY_FOR_REVIEW', 'UNRESOLVED', 'BLOCKED', 'CANCELED', 'OBSOLETE'}:
                            if time.monotonic() >= deadline:raise RuntimeError('Real repair exceeded release trial budget')
                            time.sleep(.5);run = api('GET', '/runs/' + run['run_id'])
                        report['repair_state'] = run['state']
                        report['repair_reason'] = run.get('reason_code')
                        report['baseline'] = run.get('baseline')
                        report['verification'] = run.get('verification')
                        assert run['state'] == 'READY_FOR_REVIEW', 'Real repair did not produce a verified candidate'
                        assert cart.read_bytes() == original
                        patch_id = run['candidate_id']
                        patch = api('GET', '/patches/' + patch_id)
                        assert patch['verification'] == 'PASS'
                        authority = {'approved': True, 'expected_candidate_hash': patch['candidate_hash'],
                                     'expected_base_revision': patch['base_revision'], 'idempotency_key': 'release-disposable-apply'}
                        assert api('POST', '/patches/' + patch_id + '/apply', authority)['state'] == 'APPLIED'
                        assert cart.read_bytes() != original
                        authority['idempotency_key'] = 'release-disposable-rollback'
                        assert api('POST', '/patches/' + patch_id + '/rollback', authority)['state'] == 'ROLLED_BACK'
                        assert cart.read_bytes() == original
                        assert hashlib.sha256((ASSETS / 'checks/test_cart.py').read_bytes()).hexdigest() == oracle_hash
                        report['checks'].update(real_docker_repair=True, review_before_apply=True,
                            disposable_apply=True, rollback_restores_original=True, trusted_tests_unchanged=True)
                    else:
                        assert result['decision'] in {'SANITIZE', 'REVIEW'}
                        if result['decision'] == 'REVIEW':assert result['safe_preview'] is None
                        report['checks']['privacy_contract_no_raw_secret'] = True
                    events = api('GET', '/events')
                    assert 'synthetic-release-credential' not in json.dumps(events)
                    report['checks']['redacted_audit'] = True
                    api('POST', '/scheduler/pause', {}) if args.live else None
            finally:
                if args.live:
                    subprocess.run(prefix + ['stop'], cwd=root, env=env, stdout=log, stderr=log, timeout=90, check=True)
                    report['checks']['managed_stop'] = True
                    if process is not None:process.wait(timeout=10)
                elif process is not None and process.poll() is None:
                    if os.name == 'nt':
                        from devguard.windows import signal_shutdown
                        signal_shutdown(env['DEVGUARD_SHUTDOWN_EVENT'])
                    else:
                        process.terminate()
                    process.wait(timeout=90)


if __name__ == '__main__':main()
