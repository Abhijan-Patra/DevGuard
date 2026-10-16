# Member 1 — Mac / Codex: control backend, Gemma and clipboard

Assigned to Abhijan on the M4 Mac. Branch: `codex/mac1-guard` when implementation starts.

## Ownership

`devguard/api/app.py`, `devguard/api/guard_routes.py`, `devguard/schemas/`, `devguard/guard/`, `devguard/models/`, `devguard/clipboard/`, `devguard/storage/`. Own shared package/dependency configuration and contract changes. Integrate Mac 2's router without rewriting its worker. Review scope-sensitive changes.

## Read first

[Final plan](../FINAL_PLAN.md), [model](../MODEL_DECISION.md), [contract](../API_CONTRACT.md), [clipboard](../CLIPBOARD.md), [policy](../SECURITY_POLICY.md), [coverage](../COVERAGE.md), [workflow](../TEAM_WORKFLOW.md).

## Build in order

1. Define Pydantic request/decision/event schemas from contract v1 and freeze examples with Mac 2. Create the minimal FastAPI app, scoped session auth and redacted errors.
2. Trial local `gemma4:e4b-it-q4_K_M` with actual native tool calls and privacy examples; record runtime/backend/digest and memory pressure. Use one queue with foreground priority and finite budgets.
3. Implement protected-path/destination policy, Gitleaks adapter and exact validated model spans. The model cannot override hard detector findings. Hold invalid/unavailable decisions.
4. Implement evaluate plus reference delivery gate, with bound content/task/destination/version/expiry and one-use release checks. Validate actual received payload. A safe preview alone is insufficient.
5. Implement required opt-in macOS text clipboard watcher: cheap counter checks, reads only on change, bounded text, dedupe, stale cancellation, memory-only transient state and explicit copy-cleaned with own-write suppression.
6. Add redacted findings/status/events API and capability data for Windows UI. Do not send raw clipboard content to another host without configured enrolment/consent.
7. Integrate Mac 2's real client adapter and repair router. Keep original-source apply authority outside model tools.

No screenshot/recording or keyboard monitoring. Clipboard capture stays required. No actual private content may be pasted into Codex while developing tests; use declared synthetic data.

## Handoff to teammates

- Pydantic/OpenAPI contract and examples, endpoint status and exact startup commands after code exists.
- Redacted fixture-compatible responses and clear unavailable-model behaviour.
- How Mac 2 calls the shared model queue/guard without unrestricted tokens.
- Capability matrix for installed client/capture versions.
- Model trial results and explicit unresolved issues.

## Acceptance

Actual managed delivery omits detected synthetic sensitive values; benign input remains useful; invalid model output holds; clipboard changes are version-safe; no raw values persist in logs; enabled/disabled/unsupported states are correct. Add meaningful tests for these boundaries and record actual commands/results.

## Paste into Codex

> Work on DevGuard as Member 1 on branch codex/mac1-guard. Read AGENTS.md, README.md, docs/FINAL_PLAN.md, docs/API_CONTRACT.md, docs/CLIPBOARD.md, docs/SECURITY_POLICY.md and this task file before implementation. Own shared schemas, FastAPI/auth, privacy policy, local Gemma 4 E4B, inference queue, redacted storage and opt-in macOS text clipboard capture. Keep one runtime model, gemma4:e4b-it-q4_K_M, and test it before claiming readiness. Implement real privacy classification and enforcement, not fixture-specific answers. Clipboard capture is required and optimised; screenshots/recordings and keyboard monitoring are excluded. Build the reference delivery gate before claiming other-client protection. Coordinate contract changes with Member 2; provide examples for the Windows dashboard. Preserve other owners' paths. Inspect installed versions and run focused boundary tests. Report implemented, verified, unrun and blocked items separately; never put real clipboard/secrets in commits or development prompts.
