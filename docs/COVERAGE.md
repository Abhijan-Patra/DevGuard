# Integration coverage and honest claims

Every entry starts unimplemented/unverified. Move it to VERIFIED only with installed client/runtime versions and end-to-end evidence. A plan or fixture is not evidence.

| Path | Planned control | Initial status / limit |
|---|---|---|
| DevGuard explicit text/prompt gate | Evaluate and synchronously release inspected bytes | UNIMPLEMENTED; first controlled reference path |
| macOS text clipboard capture | Opt-in counter checks, scoped scans, cleaned-copy action | UNIMPLEMENTED; advisory until a guarded send is used |
| Clipboard paste into an unrelated app | No universal interception | UNSUPPORTED; copied content can be pasted before analysis |
| Clipboard images/history | No collection | UNSUPPORTED in this build |
| Codex prompt submission | Test documented UserPromptSubmit block on installed client | UNVERIFIED; blocks/augments, not assumed arbitrary prompt replacement |
| Codex selected tool calls | Test PreToolUse for actual available tools | UNVERIFIED; inspect file, shell, MCP and alternate access separately |
| Codex automatic context, attachments, transcripts | Separate coverage investigation | UNVERIFIED; do not claim complete wire-payload interception |
| Claude Code prompt/tool integration | Optional if a Mac owner has a usable client | UNIMPLEMENTED; no new subscription required for MVP |
| Antigravity | Development assistant for Windows members | UNSUPPORTED as a protected runtime client until separately integrated |
| DevGuard guarded file/log tools | Scope enforcement and pre-delivery redaction | UNIMPLEMENTED; alternate unrestricted tools must be controlled separately |
| Independent backend repair | Source/logs/diffs/named probes/tests | UNIMPLEMENTED; no screenshot dependency |
| Screenshots and recordings | Not used | UNSUPPORTED by design |
| Pre-commit scanner | Optional configured commit path | UNIMPLEMENTED; bypassable, not complete history remediation |

## Client selection

The team already has Codex on both Macs. Mac 2 tests Codex's actual installed hook points first while Mac 1 builds the guaranteed reference gate. Do not assume a Claude client is available or delay on a subscription. Claude's documented output-replacement capability is useful for a later adapter if available.

OpenAI documents prompt blocking and selected tool hooks. Claude documents prompt blocking and tool-output replacement, while UserPromptSubmit does not directly replace the original prompt. Verify exact installed behaviour, timeouts, errors and native transcript paths. A hook adding extra context is not proof it removed the original data.

Sources: [official OpenAI hooks](https://developers.openai.com/codex/hooks), [Claude Code hooks](https://code.claude.com/docs/en/hooks). Checked 16 October 2026; installed-client compatibility is still unknown.

## Test each claim

For a managed path, prove the exact tested action is held or blocked and inspect what actually reaches the supported receiver. Use a local test receiver with declared synthetic data. A UI warning, redacted display, hook log or printed payload preview alone does not prove the original was withheld elsewhere.

Test alternate reads through shell commands, symlinks, traversal, tool results, prompts, attachments and auto-loaded instructions as separate rows. If not testable or not interceptable, show PARTIAL/UNSUPPORTED and document scope. Check crash/timeout behaviour; do not silently fail open.

An MCP server only governs its own tools. A destination firewall rule does not redact request bodies. Do not intercept/decrypt arbitrary HTTPS traffic or replace trusted certificates to manufacture coverage.
