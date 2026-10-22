"""Prepare reviewable, isolated client configs; never edit global config/trust."""
import argparse
import json
import os
import subprocess
from devguard.platform_io import private_directory
from pathlib import Path
import shlex
import sys

from devguard.client import private_token
from devguard.runtime import runtime_directory


def prepare(directory: Path, token_file: Path, base_url: str):
    # Validate both before writing anything. Never embed token bytes in config.
    token_file = token_file.absolute()
    private_token(token_file)
    # Reuse the endpoint validator without opening any network connections.
    from urllib.parse import urlsplit
    parsed = urlsplit(base_url)
    if (parsed.scheme != 'http' or parsed.hostname not in {'127.0.0.1', '::1'}
        or parsed.username or parsed.password or parsed.query or parsed.fragment
        or parsed.path.rstrip('/') != '/api/v1'):
        raise ValueError('LOOPBACK_GUARD_REQUIRED')
    directory = directory.absolute()
    if directory.exists():
        raise FileExistsError('Choose a new isolated client directory')
    private_directory(directory)
    codex = directory/'codex';private_directory(codex)
    wrapper = directory/'guard_hook.py'
    values = {'DEVGUARD_BASE_URL': base_url, 'DEVGUARD_CLIENT_TOKEN_FILE': str(token_file),
              'DEVGUARD_PROJECT_ID': 'managed-client-session',
              'DEVGUARD_DESTINATION_ID': 'local-preview', 'DEVGUARD_MANAGED_TOOLS': '1'}
    wrapper.write_text('import os\nfrom devguard.client_hook import main\n'
                       f'os.environ.update({values!r})\nraise SystemExit(main())\n')
    command = subprocess.list2cmdline([sys.executable, str(wrapper)]) if os.name == 'nt' else shlex.join([sys.executable, str(wrapper)])
    hooks = {'hooks': {event: [{'matcher': '.*', 'hooks': [{
        'type': 'command', 'command': command, 'timeout': 25}]}]
        for event in ('UserPromptSubmit', 'PreToolUse', 'PostToolUse')}}
    (codex/'hooks.json').write_text(json.dumps(hooks, indent=2)+'\n')
    args = ['-m', 'devguard.client', '--base-url', base_url, '--token-file', str(token_file)]
    (codex/'config.toml').write_text(
        'sandbox_mode = "read-only"\nweb_search = "disabled"\n[features]\nhooks = true\n'
        '[mcp_servers.devguard]\nrequired = true\n'
        'enabled_tools = ["list_sources", "read_source"]\n'
        'default_tools_approval_mode = "writes"\n'
        f'command = {json.dumps(sys.executable)}\nargs = {json.dumps(args)}\n')
    (directory/'claude-settings.json').write_text(json.dumps(hooks, indent=2)+'\n')
    (directory/'claude-mcp.json').write_text(json.dumps({'mcpServers': {'devguard': {
        'command': sys.executable, 'args': args}}}, indent=2)+'\n')
    for path in directory.rglob('*'):
        if path.is_file():path.chmod(0o600)
    return {'codex_home': str(codex), 'claude_settings': str(directory/'claude-settings.json'),
            'claude_mcp': str(directory/'claude-mcp.json'),
            'global_configuration_changed': False, 'hooks_trusted': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New private directory; never overwrites an existing profile')
    parser.add_argument('--token-file', type=Path, default=runtime_directory()/'client-token')
    parser.add_argument('--base-url', default='http://127.0.0.1:8765/api/v1')
    args = parser.parse_args()
    try:
        print(json.dumps(prepare(args.output, args.token_file, args.base_url)))
        return 0
    except (OSError, ValueError):
        print('{"error":"CLIENT_PROFILE_NOT_CREATED"}')
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
