"""Read-only prerequisites. Never reads clipboard text or sends inference input."""
import importlib.util
import platform
import shutil
import subprocess
import sys

import httpx

from devguard.config import MODEL, MODEL_DIGEST
from devguard.bootstrap import RUNNER_TAG


def diagnose(*, privacy_only=False, transport=None):
    checks = []
    def add(name, ok, action, *, required=True):
        checks.append({'name': name, 'ready': bool(ok), 'required': required,
                       'action': None if ok else action})
    add('python', (3, 11) <= sys.version_info[:2] < (3, 14), 'Install Python 3.11 or 3.12 (tested versions).')
    add('launcher_platform', sys.platform in {'darwin', 'linux'},
        'Use macOS for native clipboard capture. Windows launcher is not supported in this preview.')
    from devguard.guard.scanner import CredentialScanner
    add('credential_scanner', CredentialScanner().available, 'Install Gitleaks: https://github.com/gitleaks/gitleaks#installing')
    model_ready = False
    server_ready = False
    version = None
    try:
        with httpx.Client(base_url='http://127.0.0.1:11434', timeout=3, trust_env=False,
                          follow_redirects=False, transport=transport) as client:
            response = client.get('/api/version');response.raise_for_status()
            version = response.json().get('version')
            server_ready = isinstance(version, str)
            response = client.get('/api/tags');response.raise_for_status()
            model_ready = any(m.get('name') == MODEL and m.get('digest') == MODEL_DIGEST
                              for m in response.json().get('models', []) if isinstance(m, dict))
    except (httpx.HTTPError, ValueError, TypeError, AttributeError):
        pass
    add('ollama_server', server_ready, 'Install/open Ollama: https://ollama.com/download')
    add('pinned_model', model_ready, 'Run: ollama pull ' + MODEL + '. A different digest remains held; do not substitute a model.')
    native = sys.platform == 'darwin' and importlib.util.find_spec('AppKit') is not None
    add('native_clipboard', native, 'macOS only. Install the clipboard extra: python -m pip install ".[clipboard]"', required=False)
    docker = shutil.which('docker')
    docker_ready = False
    image_ready = False
    if docker and not privacy_only:
        try:
            docker_ready = subprocess.run([docker, 'info'], stdout=subprocess.DEVNULL,
                                           stderr=subprocess.DEVNULL, timeout=5).returncode == 0
            if docker_ready:
                image_ready = subprocess.run([docker, 'image', 'inspect', RUNNER_TAG],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5).returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            pass
    if not privacy_only:
        add('docker', docker_ready, 'Install/open Docker Desktop for repairs, or use: devguard start --privacy-only')
        add('verifier_image', image_ready, 'Run: devguard start (builds the public verifier when absent).')
    add('client_sdk', importlib.util.find_spec('mcp') is not None,
        'Optional client integration: install the client extra. See docs/CLIENT_INTEGRATION.md.', required=False)
    return {'ready': all(c['ready'] for c in checks if c['required']),
            'platform': sys.platform, 'architecture': platform.machine(),
            'python': platform.python_version(), 'ollama_version': version,
            'model': MODEL, 'expected_model_digest': MODEL_DIGEST,
            'repair_checks_skipped': privacy_only,
            'clipboard_read': False, 'inference_sent': False, 'checks': checks}
