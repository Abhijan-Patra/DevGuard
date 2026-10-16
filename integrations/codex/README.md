# Codex adapter: restrictive opt-in trial

The installed client check on 16 October 2026 found `codex-cli 0.162.0-alpha.17.2` and the hooks feature enabled. This is capability inspection, not evidence that this adapter has run inside a real Codex session.

`hook.py` accepts the documented command-hook JSON on stdin. Unit/process tests exercise its output contract. No `.codex` files or global configuration are installed by this branch.

## Current behaviour

- UserPromptSubmit sends bounded prompt text to the configured loopback Mac 1 guard. Only a ready, unexpired, destination/version-matching ALLOW lets the unchanged prompt continue. SANITIZE, LOCAL_ONLY, REVIEW, BLOCK, missing credentials, malformed responses or unavailable guard produce a constant redacted block. Cleaned text must be resubmitted explicitly.
- PreToolUse denies **all** calls in this initial trial. A classifier cannot authorize arbitrary shell/file access. This restricts normal coding functionality; it is not a completed productive managed-tool integration.
- PostToolUse checks a supported tool result and blocks the model-visible result on held checks. It cannot reverse side effects or prove deletion from native transcripts/telemetry.
- No prompt/result content or token is printed in diagnostics. The HTTP client refuses redirects, proxies and remote guard destinations.

## Manual activation after Mac 1 integration

1. Review the script. Install the trusted hook outside the coding agent's writable project boundary for meaningful enforcement.
2. Set `DEVGUARD_BASE_URL` to a loopback `/api/v1` endpoint, `DEVGUARD_PROJECT_ID`, the configured `DEVGUARD_DESTINATION_ID`, and a **scoped adapter** `DEVGUARD_ADAPTER_TOKEN`. Keep tokens out of Git, command history and model tools; do not use the operator apply token.
3. Adapt absolute paths in `hooks.example.json`, then review the merge with existing project hook configuration. The example is not an automatic installation command.
4. In the intended local Codex client, inspect `/hooks` and explicitly review/trust the exact definitions. Do not bypass hook trust. Test declared synthetic input and actual held/released payloads.
5. Record installed client/version, trust status, exact event path, timeout/crash behaviour and safe receiver evidence. Leave broader coverage UNVERIFIED/PARTIAL.

Codex can skip untrusted hooks, and callback errors/timeouts are not a complete fail-closed security boundary. Multiple hooks can run concurrently. Hosted tools, automatic context, attachments, session transcripts and alternate paths need separate assessment. An otherwise unrestricted desktop agent remains outside this adapter's containment. Use OS/tool restrictions as the actual boundary.

Source: [official OpenAI hooks documentation](https://learn.chatgpt.com/docs/hooks), checked 16 October 2026. The script uses documented prompt blocking and tool denial; live installed-client behaviour is pending verification.
