# Mac 1 implementation handoff

Branch: `codex/mac1-guard`. Pull request: [DevGuard #1](https://github.com/Abhijan-Patra/DevGuard/pull/1). Status on 16 October 2026: backend controls implemented; Gemma download independent and still pending at validation; native clipboard capture remains OFF.

## Implemented

- Typed, bounded guard/clipboard schemas with strict versions and fixed decision/category enums.
- Fast baseline rules plus installed Gitleaks 8.30.1. Gitleaks runs through stdin/stdout in an empty temporary working directory; repository allowlists and `gitleaks:allow` cannot downgrade it.
- Codepoint-span redaction, no model-provided replacement text, no free-form model reasons in audit output, final scanner checks.
- Contextual Gemma adapter that validates its JSON schema, holds unavailable/invalid/oversize analysis and never falls back to another model or scripted answer.
- Immutable inspected candidate, owner/version/destination/policy/expiry checks, one-use delivery, no automatic retry after an ambiguous receiver failure, no arbitrary URL registration.
- Scoped optional adapter credential and a separate operator credential. Authentication, validation and body-budget errors do not echo private inputs.
- Redacted metadata events in bounded in-memory SQLite; ephemeral candidates expire and are revoked on source/capture changes.
- Descriptor-anchored approved-file reads with protected paths, size/type checks and no-follow directory/file traversal. Mac 2 must pass read text through guard evaluation before model/client delivery.
- Lazy native macOS text clipboard adapter; explicit consent, no initial-content read, 750 ms counter polling, 250 ms debounce, duplicate suppression, generation/version cancellation, expiry, explicit cleaned copy and own-write suppression. No screen, recording or keyboard hooks.

## Actual validation

`pytest -q`: **38 passed**, with one upstream TestClient deprecation warning. Most checks intentionally inject a scanner/model/clipboard double to test enforcement; they are not model accuracy or native capture benchmarks. Integration tests also exercise the real cross-thread guard bridge and operator-only auth on an injected synchronous router.

One test uses the actual installed Gitleaks binary and a declared synthetic provider-shaped token, including a `gitleaks:allow` comment, and confirms detection/redaction. A live API probe using synthetic password text produced REVIEW with CREDENTIAL and MODEL_UNAVAILABLE; delivery returned 403 and the value was absent from response/audit events.

The native bridge imports and exposes the required APIs. The live control CLI reports supported macOS capture and OFF. No user clipboard text has been read or overwritten in development validation. Do not label real capture/copy behaviour VERIFIED until the operator explicitly enables it and tests it with synthetic copies.

## Running endpoints

The local server runs at `http://127.0.0.1:8765`. `/health` is public; all other listed endpoints require credentials.

| Endpoint | Implemented result |
|---|---|
| GET /api/v1/status | Runtime, scanner, capture and incomplete-feature status |
| GET /api/v1/coverage | Partial local guard/capture; client and repair unimplemented |
| POST /api/v1/guard/evaluate | Sanitised decision view or held request |
| POST /api/v1/guard/requests/{id}/deliver | Only a trusted enrolled receiver and a valid owned inspection can release |
| GET /api/v1/findings | Transient redacted operator decision views |
| GET /api/v1/events?after=0 | Bounded metadata events; process-local cursor |
| GET /api/v1/clipboard/status | No new clipboard text read |
| POST /api/v1/clipboard/enable | Local operator + explicit consent, watches future copies |
| POST /api/v1/clipboard/disable | Cancel queued work and clear transient originals/candidates |
| POST /api/v1/clipboard/copy-cleaned | Local operator, exact version and completed inspection required |

## Mac 2 integration

Use the [exact integration signatures and synchronous worker bridge](MAC_2_INTEGRATION.md). The pushed Mac 2 worker interfaces have been inspected; repair code has not yet been merged or mounted.

Import `GuardInput`, `GuardEngine`, `ProjectFiles` and the app factory. Enrol receiver callables in trusted startup code using `create_app(..., receivers={"configured-client": receiver})`. A receiver is an async callable accepting the inspected text; it does not receive a model-selected URL or operator token. It must perform its actual supported delivery and report failure by raising. Never pass unscanned file reads/tool output directly to the coding model.

Use a separately generated `DEVGUARD_ADAPTER_TOKEN` in a local, ignored environment. Requests made with it are owned by `adapter`; operator request IDs cannot be released using that credential and vice versa. No adapter is configured by default and no client-coverage claim is made.

Mac 1 still registers the repair router into the app when Mac 2 supplies it. The model adapter currently serialises calls; foreground/background scheduling priority is not yet integrated with the repair worker.

## Windows integration

Use actual response shapes in the shared contract. UI actions display authoritative failures and expiry; a pending MODEL_UNAVAILABLE is not safe. No raw history, fake confidence or fabricated success. Native capture lives on the Mac; a remote Windows viewer does not silently enable/copy its clipboard. Scenario records and UI fixtures remain labelled until backed by live evidence.

## Remaining limits

Real Gemma inference/accuracy and tool roundtrip, real client hooks/delivery, live native clipboard read/write, project registration/scanning, durable metadata persistence and repair remain to be verified or implemented. Large contextual payloads are held rather than truncated. Native paste interception and global atomic clipboard writes are not promised.
