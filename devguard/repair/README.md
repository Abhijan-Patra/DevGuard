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

Mac 1's newly published foundation at `3b50bd9` selects the explicit `gemma4:e4b-it-q4_K_M` package and API port 8765. This branch matches those choices. `devguard/agent/mac1_bridge.py` adapts the published asynchronous `OllamaClient.inspect()` and `chat(messages, tools=...)` to the synchronous worker. Construct `Mac1ModelBridge(client, asyncio.get_running_loop(), await client.inspect())` during application startup, then call it from the worker thread. It uses the same client/lock, checks the digest before each call and requires one complete native tool call. There is no duplicate Ollama client or inference server. The foundation has no guard or scoped adapter credentials yet; these are still required before a live repair/client-protection claim. Mac 1 must also add foreground queue priority.

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
