# Mac 2 implementation and integration handoff

This branch implements the first repair worker and restrictive Codex hook adapter. It does not implement Mac 1's privacy classifier, model queue, shared schemas, clipboard service or application startup.

## Implemented

- Explicit source-file snapshots including saved uncommitted changes, hashes, size limits, protected paths, symlink/hardlink rejection and private temporary storage.
- Typed, bounded investigation tools: list approved files, read approved source, run a named check, propose a sandbox replacement and finish. Initial limits: eight actions, two patch proposals, 180-second investigation budget plus finite verifier runs. The model adapter must enforce its own request timeout.
- Restricted Docker verifier: immutable image ID, no automatic pull, no network, non-root user, dropped capabilities, read-only source/tests/root, bounded memory/processes/output and timeout/cancellation cleanup. No host-shell fallback.
- Independent baseline and final checks. Healthy or unreproduced failures never become successful patches.
- Scanned single-file candidates, operator-only application, base checks over every captured source file, atomic file replacement, rejection and idempotency. Originals remain untouched until application.
- Deduplicated incidents/runs, a single background worker, manual idle trigger, pause/cancellation and debounced monitoring of the approved source manifest.
- Repair router matching the proposed `/api/v1` routes, with injected operator authorization and fixed redacted errors. It mounts in Mac 1's app.
- Declared buggy FastAPI cart fixture and protected business-behaviour tests, including quantity multiplication, empty/null cart and validation.

This is an initial implementation, not a completed live Gemma repair demonstration. Unit tests deliberately inject fake ports to test authority/lifecycle boundaries. They are not evidence of model accuracy. The trusted demo checks intentionally fail against the buggy fixture.

## Recorded local verification — October 16, 2026

- Apple M4 / 16 GB; Python 3.12.14; Docker Desktop 4.95.0, engine 29.8.2; Gitleaks 8.30.1 installed.
- Mac 2 unit suite: **79 passed**, one integration module skipped because Mac 1 source is absent on this branch.
- Temporary combined source using Mac 1 `2f28880` and this worker: **118 passed**, including the actual app/auth binding and installed Gitleaks fixture check. Model HTTP responses are mocked in these tests; native clipboard capture remains disabled.
- Real restricted Docker run over an approved snapshot: **FAIL / exit 1**, **4 failed, 3 passed**, as required for the declared buggy cart baseline. All seven checks ran with no network and the prepared dependencies. No model was used and original source was unchanged.
- Built local ARM64 verifier image: `sha256:c74d2d570e55537d0b57d10c8c079834dbacf14b10a7e79768edebf6733aa6c7`. This ID is local, not a published registry image; other machines build/inspect their own image.
- Actual serialized guard inputs for this Docker evidence measured **1,554 bytes** for baseline evidence and **1,620 bytes** for the named-test tool result, below the published 2,048-byte limit. Larger/different outputs can still hold.
- Ruff checks and `git diff --check` passed. Pytest emits a dependency deprecation warning about Starlette's HTTPX TestClient.

Still unverified: genuine shared Gemma repair, live coding-client interception, foreground-priority scheduling and durable/supervised application integration. These are readiness gates, not implied by the passing unit checks.

## Local commands

From the repository root, use Python 3.12:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r tests/backend/requirements-dev.lock
.venv/bin/python -m pytest tests/backend -q
.venv/bin/ruff check --isolated --select E4,E7,E9,F,I devguard/agent devguard/monitor devguard/repair devguard/api/repair_routes.py integrations/codex demo/backend trusted_tests tests/backend
.venv/bin/python -m devguard.repair doctor
```

The local development environment may use the desktop app's bundled Python 3.12 executable to create this venv. No shared root dependency configuration is changed. Mac 1 should reconcile the scoped lock file with the shared dependency lock.

After Docker Desktop's first-run setup and engine startup:

```sh
.venv/bin/python demo/backend/build_runner.py
docker image inspect devguard-runner:mac2 --format '{{.Id}}'
.venv/bin/python -m devguard.repair baseline --image-id sha256:REPLACE_WITH_ACTUAL_IMAGE_ID
```

The build helper sends only the Dockerfile and scoped dependency lock to Docker. Runtime does not install dependencies. A baseline `FAIL`/exit 1 is expected for this declared buggy demo; a Docker/setup error is not a reproduced application failure. Record the actual resolved image ID. Do not use `python:latest` as a runtime verifier image.

## Exact interfaces requested from Mac 1

Internal protocols live in `contracts.py`. They are provisional integration boundaries, not replacements for the shared schemas.

1. `GuardPort.sanitize(text: str, *, purpose: str) -> str`: approve/sanitize locally for `snapshot_source`, `test_evidence`, `tool_result` and `patch_export`; raise `RepairError` on held/unavailable checks. A SANITIZE response must return approved bytes, never an unvalidated preview. Source requiring sanitization is held before writing a snapshot; the worker also requires an unchanged approved patch diff for export/application.
2. `ModelPort.metadata`: actual `{"name": "gemma4:e4b-it-q4_K_M", "digest": "<installed digest>"}`. `next_action(messages, tools) -> {"tool": name, "arguments": {...}}` calls the existing shared queue with a finite timeout. Normalize a genuine native function call into that object; do not use a fixture lookup. Honor foreground privacy priority in the shared queue. Do not return or persist hidden reasoning.
3. A synchronous FastAPI `require_operator` dependency that rejects adapter/model scope. Mount `create_repair_router(service, require_operator)` once. The router does not create a second server or expose model tools that can call apply.
4. `event_sink(event)` for durable redacted event storage and the existing events endpoint. This branch initially retains run/candidate state only in memory; restart does not resume or apply work. It caps retained runs at 64 and incidents at 256, then holds new work pending operator cleanup/restart. Event-store failures block work and pause the scheduler.

The selected model is the explicit `gemma4:e4b-it-q4_K_M` package and the API port is 8765. `devguard/agent/mac1_bridge.py` adapts Mac 1's asynchronous `inspect()` and `chat(messages, tools=...)` to the synchronous worker, using the same client/lock, checking the digest before each call and requiring one complete native tool call. There is no duplicate Ollama client or inference server.

### Mac 1 application binding, checked against `2f28880`

The guard/scoped auth and `RepairGuardBridge` now exist. Read Mac 1's `docs/MAC_2_INTEGRATION.md`; the following helper uses its exact app-state ports without changing Mac 1's files:

```python
from devguard.repair.mac1_binding import build_mac1_binding

# Inside the running app startup; trusted_verifier_specs is operator configuration.
service, router = build_mac1_binding(
    app,
    loop=asyncio.get_running_loop(),
    runtime_root=private_runtime_directory,
    project_specs=trusted_verifier_specs,
    readiness_check=verified_integration_capabilities,
)
app.include_router(router)  # Mac 1 owns mounting once.
```

The helper uses `app.state.model_queue`, the actual `RepairGuardBridge(app.state.guard, loop, RepairError)`, and `app.state.operator_auth`. A deferred model bridge performs no inference/readiness query during server startup; absent weights hold the later job without preventing privacy-server startup. Calls to guard/model ports and operator repair actions run off the app loop.

`verified_integration_capabilities()` must return actual boolean values for `foreground_priority`, `durable_events`, `worker_lifecycle` and `trusted_verifier`. Default values are false. Missing gates cause HTTP 503 on Enter idle and WAITING_FOR_RESOURCES for attempted jobs; source/model execution does not begin. HTTP clients cannot set these flags. Do not turn them on merely to make a demonstration run.

The default `Mac1AuditEventBridge` schedules constrained kind/state records through Mac 1's existing audit writer on the app loop. It never passes raw summaries or writes a competing schema. An in-memory audit cannot satisfy the durability gate, even if a caller says it is durable. The current central audit schema lacks run/project/tool fields: run IDs remain in repair responses and `completed_tools` in run views; enriching central event associations needs Mac 1's schema coordination. A custom durable, constrained sink can be supplied explicitly.

Mac 1 must supervise shutdown before closing audit/model/guard resources: `stopped = await asyncio.to_thread(service.shutdown, 30)`. Check the returned result; false means the worker has not stopped and lifecycle readiness has not been established. Shutdown pauses/cancels work and clears retained original/replacement bytes once the worker stops. Do not start a second app/model server.

Mac 1's current inference lock serializes requests but is not yet a foreground-priority queue. Its default audit is in memory. Keep execution paused until these gates, trusted image configuration and lifecycle wiring are implemented and verified. The first contextual privacy budget is 2 KiB of serialized task/text; oversized evidence holds rather than silently truncating. Named Docker checks run every test, use one-line failure reports and omit warning/header noise. A separate temporary bytecode prefix prevents loading host bytecode caches with stale source paths.

Trusted application startup constructs a `RepairService`, registers `ProjectSpec` configurations and mounts the router. Registration comes from the operator-selected project, not model arguments or arbitrary UI roots. The demo registration helper is `demo.backend.config.demo_project(repository_root, image_id)`.

An actual trial can use an operator-supplied integration factory returning that configured service:

```sh
.venv/bin/python -m devguard.repair trial --factory YOUR_TRUSTED_MODULE:create_service --project demo-cart --signal cart
```

`YOUR_TRUSTED_MODULE` is an integration placeholder, not a file supplied by this branch. The CLI never substitutes a fake or hosted model when integration is missing. Trial mode produces a review report, never applies a patch. Application requires the live operator API.

## Run/application behaviour

Create a named incident, queue investigation, then invoke the manual idle endpoint to drain background work. The scheduler initially starts paused. A foreground resume can pause and cancel heavy work; the shared model queue must prioritize guard requests.

Only one changed source file is accepted initially, allowing atomic replacement. Changes to any captured dependency invalidate a candidate. A DevGuard lock coordinates DevGuard writers; editors that ignore that lock still have a narrow check/replace race. This is best-effort conflict protection, not a filesystem transaction against arbitrary concurrent applications. Multi-file transactions and persistent recovery are unfinished.

Keep trusted tests, runtime policy, model adapter and tool definitions outside the model-writable source scope. The first demo writes only `cart.py`; `main.py` and tests remain fixed. Passing these tests establishes only their checked behaviour, not production correctness or resistance to arbitrary malicious Python instrumentation.

Wire `SavedFileMonitor.tick()` into the supervisor lifecycle with configured project and signal. It creates signals after saved files settle; automatic OS-idle/resource heuristics, arbitrary production probes, additional log adapters and 24/7 hosting are later work. A sleeping/shut-down laptop cannot run overnight repairs.

## Before claiming a live milestone

Run real Gemma actions through the shared adapter, record actual digest/settings, reproduce the baseline inside Docker, verify the genuine patch with unchanged checks, inspect exports, demonstrate stale rejection and cancellation, then document the real result. Do not substitute unit-test fake ports or prewritten successful repairs into the demo.

For the coding-client trial, see `integrations/codex/README.md`. Root README/planning status and shared coverage docs need an owner-reviewed update when this branch is integrated; they should not be interpreted as code verification.
