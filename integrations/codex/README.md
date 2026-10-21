# Native client hook and managed source tools

The packaged hook is `python -m devguard.client_hook`; `hook.py` remains a compatibility entrypoint. No global configuration or hook trust is installed automatically.

See [the current integration guide](../../docs/CLIENT_INTEGRATION.md) for isolated profiles, supported commands, measured native CLI versions, actual receiver evidence and limitations. The old all-tools-denied prototype now has an explicit opt-in for the two guarded MCP source tools. Native shell/file/edit tools remain denied.

The guard HTTP timeout is 20 seconds inside a 25-second hook budget. Only an exact unchanged READY/ALLOW can pass a prompt. Missing dependencies, mismatched bytes, malformed replies or held decisions produce constant feedback without echoing the input. The server enforces the managed source output boundary before disclosure.

Recorded CLI boundary tests use a local synthetic coding-provider transport and the **real** local Gemma guard. They do not establish universal interception, desktop/IDE coverage, transcript removal or signed-in cloud-client delivery.
