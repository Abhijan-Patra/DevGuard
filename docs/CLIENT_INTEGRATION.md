# Scoped coding-client integration

21 October 2026. This runs entirely on the one Mac. The DevGuard runtime still uses only the pinned local Gemma E4B Q4 package.

## Supported workflow

`devguard.client` is a stdio MCP server with exactly two tools:

- `list_sources()` returns registered project IDs and relative source paths.
- `read_source(project_id, path)` reads one registered file through the real guard, final credential scan, source-hash recheck and one-use release. It returns approved text or a constant held result. It cannot run commands, choose an arbitrary URL/root, modify source, change policy or apply patches.

The native hook checks submitted prompts for sensitivity. Only a ready, unexpired ALLOW with an exact preview match permits the unchanged prompt. SANITIZE requires explicit cleaned resubmission. Native shell, filesystem, editing and other MCP tools are denied; opting into managed tools permits only the two exact DevGuard names above. Managed output is inspected **inside the server before it reaches the client**, rather than trusting a post-tool warning to remove something already disclosed. Hooks without a separately supplied task perform sensitivity checks only; the dashboard also supports explicit task relevance.

The CLI now creates a separate private `.devguard/client-token`. It has guard/client authority and cannot access operator status/composer, enable capture, execute repairs or apply patches. Its bytes never go in a model tool definition or generated config. Existing environment-provided adapter tokens remain supported; supply their matching private file explicitly when generating profiles.

## Prepare isolated profiles

From the reviewed DevGuard installation:

```sh
.venv/bin/python -m pip install -r requirements-client.lock.txt
.venv/bin/python -m pip install --no-deps -e .
./scripts/devguard-local start
.venv/bin/python -m devguard.client_config --output .devguard/client-profiles
```

The output directory must be new. It contains a Codex config/hooks file, Claude settings/MCP config and a reviewed hook wrapper; it contains the **token file path, not its bytes**. No existing/global client settings, auth files or trust database are edited. Keep the installation/config outside any coding agent's writable project for meaningful tamper resistance. Do not register the DevGuard installation, runtime directory, secrets or client config as project source.

Codex CLI: review the generated files, use their `codex` directory as the isolated `CODEX_HOME`, sign in there if necessary, and open `/hooks` to review/trust the exact definitions. Use the normal interactive client; no hook-trust or sandbox bypass flag is needed. Its profile uses a read-only sandbox, disabled hosted web search and an exact read-only MCP tool allowlist. Trust is **not** preinstalled by DevGuard.

Claude Code: use normal account sign-in and start in a clean project with the generated files:

```sh
claude --setting-sources "" \
  --settings /absolute/client-profiles/claude-settings.json \
  --strict-mcp-config --mcp-config /absolute/client-profiles/claude-mcp.json \
  --tools "" --allowedTools mcp__devguard__list_sources mcp__devguard__read_source
```

Review existing integration/trust prompts in that client. Built-in tools stay disabled in this workflow. The two managed tools support source investigation and context delivery; they do not turn the external assistant into an unrestricted repair executor. Use DevGuard's reviewed repair dashboard for actual apply/rollback.

## Measured scope

See [native trial metadata](evidence/professional-native-clients.json). The installed bundled Codex CLI `0.163.0-alpha.10.2` and Claude Code `2.1.119` were exercised with actual native hook events and MCP calls. The Homebrew Codex `0.132.0` was inspected but is not the tested bundled version.

The coding-provider endpoint in these tests was a **local synthetic protocol fixture**, not a cloud coding model. The guard and source inspections used **real pinned Gemma and Gitleaks**. A benign positive control verifies connectivity; synthetic sensitive prompts are held before provider POST; managed clean source reaches the receiver; detected source credentials are absent from the subsequent provider request. Native event/result metadata is recorded without private text. This proves those configured CLI boundaries, not cloud-model behavior or a real signed-in account workflow. No general clipboard access or global configuration change occurred.

## Limits that remain

Non-managed hooks can be skipped until trusted. A hook process that cannot start, crashes or times out can fail open at the native-client layer. The script handles its own HTTP/model failures with a constant block before its 25-second hook budget, but it cannot guarantee that an external client will run it. The MCP server independently holds failed scans/reads even without a hook.

Automatic context, attachments, hosted tools, specialized alternate tool paths, desktop/IDE variants, transcripts and telemetry are outside these measurements. An otherwise unrestricted app can bypass this workflow. PostToolUse cannot undo a tool's side effects; do not use it as the primary source-read boundary. On this installed Claude version, do not assume newer documented hook failure controls are available. Windows native text capture now has a separate implementation and CI gate; see [Windows setup](WINDOWS.md). The Mac client trials above do not establish Windows signed-in coding-client protection.

Sources checked for implementation: [OpenAI hooks](https://learn.chatgpt.com/docs/hooks), [Codex MCP configuration](https://learn.chatgpt.com/docs/extend/mcp?surface=cli), [Claude hooks](https://code.claude.com/docs/en/hooks), [official MCP SDK](https://py.sdk.modelcontextprotocol.io/v1/).
