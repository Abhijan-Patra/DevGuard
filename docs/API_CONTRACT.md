# Shared API and event contract v1

Owner: Mac 1. Mac 2 and both Windows owners implement against this document. Guard, event and clipboard routes now exist on the Mac 1 branch. Repair routes are mounted through the trusted integration runtime; general project registration and saved-file scanning remain proposed. The implemented Pydantic schemas live in `devguard/schemas/guard.py`; executable usage and limitations are in [MAC_1_IMPLEMENTATION.md](MAC_1_IMPLEMENTATION.md). Change the version for incompatible fields.

## Conventions

The implemented `/status` also includes `inference_queue`: `active`, `foreground_waiting`, `background_waiting`, `capacity` and `closed`. These contain counts/flags only. Foreground privacy overtakes waiting repair calls; active inference is not preempted. This scheduling status is not model-readiness or completed-protection evidence.

Base prefix `/api/v1`; JSON; IDs are opaque strings; UTC ISO-8601 timestamps. Backend uses relative safe display paths. Requests with text are sensitive and must not be logged. All endpoints except `/health` require a scoped `Authorization: Bearer <session-token>` header; tokens never appear in URLs, fixtures or Git. Streamlit holds its token server-side. Model tools cannot call operator APIs.

Errors use `{ "error": { "code": "STALE_CONTENT", "message": "Content changed; rescan required", "request_id": "req-example" } }` with no sensitive values. Use 400 validation, 401/403 auth/policy, 404 absent resource, 409 stale/conflict, 413 oversize and 503 unavailable dependency. A 200 evaluation response is a decision, not permission to bypass the gate.

## Privacy endpoints

| Endpoint | Request / result | Authority |
|---|---|---|
| GET /health | Readiness including `model_ready`; no private details | Public loopback |
| POST /projects | Operator-selected root and policy ID -> project ID | Operator |
| GET /status | Redacted worker/model/capture status and capability list | Operator/UI |
| POST /guard/evaluate | Bounded input and context -> decision view; never sends input externally | Operator or scoped adapter |
| POST /guard/requests/{id}/deliver | Expected version/destination -> delivery receipt | Enrolled adapter through verified gate |
| GET /findings?project_id=... | List of redacted findings | Operator/UI |
| GET /events?after=... | Cursor and redacted events; simple polling | Operator/UI |
| GET /coverage | Capability statuses from actual runtime/version checks | Operator/UI |

Evaluation input example (synthetic; IDs are illustrative):

```json
{
  "project_id": "project-demo",
  "task": "Diagnose the login exception",
  "surface": "explicit_prompt",
  "destination_id": "configured-coding-client",
  "content_version": 7,
  "text": "ValueError at login.py:42; user email is person@example.invalid"
}
```

Allowed surfaces: `explicit_prompt`, `tool_result`, `file_read`, `clipboard`. The adapter authenticates metadata; a UI-submitted surface label alone does not prove interception. Destination IDs resolve to trusted configuration; caller-supplied URLs cannot turn the gate into an arbitrary proxy.

Decision view example, explicitly not an actual inference result:

```json
{
  "request_id": "request-demo",
  "content_version": 7,
  "policy_revision": "policy-v1",
  "destination_id": "configured-coding-client",
  "decision": "SANITIZE",
  "safe_preview": "ValueError at login.py:42; user email is CUSTOMER_1",
  "reason_codes": ["PERSONAL_DATA"],
  "finding_ids": ["finding-demo"],
  "status": "READY",
  "expires_at": "2026-10-16T12:00:00Z",
  "delivered": false
}
```

Decisions: ALLOW, SANITIZE, LOCAL_ONLY, REVIEW, BLOCK. Evaluation status: CHECKING, READY, FAILED, EXPIRED. An evaluation ID is not a bearer release token. Internally bind raw/cleaned bytes, task, version, policy revision and destination in bounded memory. Deliver checks identity, expiry, current content and one-use status. No client may substitute new bytes after evaluation. If a native hook supports only blocking, the response offers cleaned text for resubmission and records `delivered: false`.

Internal model proposals contain classification/reason codes and `{start,end,replacement,category}` spans with zero-based Python Unicode-codepoint offsets into the immutable text. Validate range, overlap and exact content version in Mac 1 code before applying. Never expose original sensitive spans in audit responses.

## Clipboard endpoints

| Endpoint | Input / result |
|---|---|
| GET /clipboard/status | Current enrolled host, enabled flag, state, version, supported type and safe preview |
| POST /clipboard/enable | Explicit local operator consent, host and optional task/project binding |
| POST /clipboard/disable | Stop reads, cancel work and clear transient originals |
| POST /clipboard/copy-cleaned | Expected content version -> copied/new version, or 409 without mutation |

Native enable/copy actions are local-operator-only and target the capture host; a remotely connected Windows UI displays status and cannot silently read or replace another machine's clipboard. The capture host must explicitly confirm these actions. Frontend fixture mode simulates them visibly and has no native access.

Clipboard states: OFF, CHECKING, SENSITIVE, REVIEW, CLEAR_FOR_CAPTURE_SCOPE, SKIPPED, ERROR. Include `capture_host_id`, `content_version`, `state`, `enabled`, `redacted_summary`, `finding_ids`, `can_copy_cleaned`. Never return original text, raw history or a reversible map. Copy-cleaned is not model delivery.

## Repair endpoints

| Endpoint | Request / result |
|---|---|
| POST /incidents | Project ID, named signal/reproduction and source revision -> incident ID |
| POST /incidents/{id}/investigate | Queue bounded run -> 202/run ID |
| GET /runs/{id} | State, safe observations, model digest, verification and candidate IDs |
| POST /runs/{id}/cancel | Idempotent cancellation request |
| GET /patches/{id} | Scanned unified diff, base hashes and verification summary |
| POST /patches/{id}/apply | Operator confirmation, expected candidate hash/base revision -> applied or 409 |
| POST /patches/{id}/reject | Reject candidate |
| POST /scheduler/pause | Pause heavy work; foreground guard remains available |
| POST /scheduler/enter-idle | Explicit demo trigger; no permission elevation |

Run states: QUEUED, WAITING_FOR_RESOURCES, SNAPSHOTTING, INVESTIGATING, PATCHING_SANDBOX, VERIFYING, READY_FOR_REVIEW, APPLIED, UNRESOLVED, BLOCKED, CANCELED, OBSOLETE, REJECTED. Responses carry the current state, not an invented progress percentage. Application is operator-only; idempotency key and candidate/base checks prevent double application.

## Event schema

Required fields: `schema_version`, `event_id`, `timestamp`, `project_id` (nullable for unbound clipboard), `kind`, `state`, `severity`, `redacted_summary`, `evidence_refs`. Optional `request_id`, `run_id`, `content_version`, `snapshot_hash`, `capture_host_id`. No arbitrary raw payload field.

Kinds: `guard.decision`, `clipboard.changed`, `clipboard.decision`, `run.state`, `tool.completed`, `verification.completed`, `patch.state`, `integration.coverage`. Evidence references resolve only to redacted records. Poll response: `{ "events": [], "next_cursor": "cursor-example" }`. Cursors are opaque; consumers deduplicate event IDs.

## Coverage entries

Each has `capability`, `client`, `client_version`, `status`, `verified_at`, `evidence_ref`, `limitations`. Status is `UNIMPLEMENTED`, `UNVERIFIED`, `VERIFIED`, `PARTIAL` or `UNSUPPORTED`. Initial documentation does not mark any implementation VERIFIED.

## Fixture rule

Windows 1 builds views from examples and synthetic events under a persistent FIXTURE MODE banner. Windows 2 supplies fixture content matching this schema. Fixture content is presentation data, never a runtime classification lookup or proof of delivery/repair. Mac 1 reviews schema changes and Mac 2 validates backend acceptance cases.

## Current implementation details

- `local-preview` is the only default destination. It returns no outgoing delivery; `/deliver` holds unless trusted server code enrols a receiver. There is no API to register arbitrary URLs.
- Optional `DEVGUARD_ADAPTER_TOKEN` is distinct from the operator token and can evaluate/deliver only its own request IDs. It cannot inspect operator findings or change capture state. Native actions also require a loopback operator request.
- Validation errors omit original values; oversized HTTP bodies return 413. The source text limit is 32 KiB, while the first contextual inspector holds serialised task/text input above 2 KiB rather than silently truncating it.
- The CLI uses private persistent SQLite with 5,000-event retention. `create_app` defaults to in-memory audit storage for explicit test/embed use unless a store is injected. Only constrained redacted metadata persists; raw previews/clipboard/candidate/work state never persist. Findings are transient in-memory decisions, not a persistent project tracker; project filtering is not implemented yet.
- Native capture starts OFF and observes future copies after consent. It does not inspect the clipboard that was already present at enable time.
- Delivery/owner/replay logic has synthetic boundary tests; real model decisions and a real coding-client receiver remain unverified. Do not infer those from a successful backend response.

## Integrated repair setup

`GET /incidents` returns `{ "incidents": [], "repair": { "configured": false, "available": false, "state": "UNAVAILABLE", "reason_code": "REPAIR_NOT_CONFIGURED" } }` until trusted startup configures a real service. `GET /status` includes `repair` and `audit` metadata. Existing mutation/run/patch routes remain operator-only and return a held dependency error when unconfigured. `POST /repair/initialize` retries the startup-supplied configuration; no request can choose a root or verifier image. See [integration status](INTEGRATION_STATUS.md).


## Measured model package pin

The authenticated status `runtime` now adds `expected_model_digest` and `reason_code` (`MODEL_READY`, `MODEL_NOT_INSTALLED`, `MODEL_DIGEST_MISMATCH` or `MODEL_RUNTIME_UNAVAILABLE`). A matching tag alone no longer makes `model_ready` true. The shared model client rechecks the installed digest after queue admission and before each inference POST; mismatch holds without posting the input. These are additive status fields; request and repair adapter interfaces remain unchanged.

The live dashboard validates the actual status envelope (`phase` plus typed `runtime`) before rendering text/action controls. Incompatible standalone mock servers require labelled Fixture Mode for rehearsal; this compatibility check does not authenticate arbitrary local software.
