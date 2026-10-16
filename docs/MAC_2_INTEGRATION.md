# Exact Mac 1 interfaces for Mac 2

Branch: `codex/mac1-guard`; PR [#1](https://github.com/Abhijan-Patra/DevGuard/pull/1). The queue, guard and auth instances are available after `create_app(settings)` through `app.state`. This file describes actual code, not a guessed worker protocol.

The current integration branch is `codex/mac1-integration`, based on main with both Macs and Windows 1 merged. The synchronous worker protocols remain unchanged. Repair routes are mounted with a held runtime until trusted startup supplies the real service; see [current integration status](INTEGRATION_STATUS.md).

## Gemma interface

```python
from devguard.models.ollama import OllamaClient, ModelUnavailable

async def chat(
    messages: list[dict],
    *,
    tools: list[dict] | None = None,
    output_format: dict | None = None,
    priority: str = "background",  # foreground / background
) -> dict: ...

model_chat = app.state.model_queue.chat
```

Return shape is the Ollama result, including `result["message"]`, optional `message["tool_calls"]` and runtime timing fields. Parse tool arguments using your own typed tool registry and permitted actions. Do not log raw bodies/hidden reasoning. `ModelUnavailable` is a fixed safe exception; propagate cancellation normally.

Settings: exact `gemma4:e4b-it-q4_K_M`, loopback only, 4,096 context and 512 output tokens initially. One bounded queue serialises calls, with 16 waiting slots. Privacy inspection uses `foreground`; existing repair calls default to `background`. Foreground work overtakes waiting background work; each class keeps FIFO order. An active Ollama call is not preempted. A privacy deadline still holds the request if active work takes too long. Queue capacity/closure failures raise `ModelUnavailable`; canceled waiting calls are removed before any HTTP request. Do not hold a separate queue/inference lock while calling the privacy guard: its contextual inspection uses the same model internally. Larger budgets need coordination and measurement.

Reuse your existing `devguard.agent.mac1_bridge.Mac1ModelBridge`; its `inspect()` and `chat()` calls match this client. Construct it on the running app loop using the installed runtime metadata. If the model/digest is missing, hold repair startup/readiness rather than invent metadata or prevent the privacy server from starting.

## Privacy guard

```python
from devguard.guard.engine import GuardEngine, GuardError, Inspection
from devguard.schemas.guard import GuardInput, Decision

async def evaluate(
    request: GuardInput,
    *,
    owner: str = "operator",
) -> Inspection: ...

guard = app.state.guard
inspection = await guard.evaluate(
    GuardInput(
        project_id=None,
        task="Diagnose the failing operation",
        surface="tool_result",  # or file_read / explicit_prompt / clipboard
        destination_id="local-preview",
        content_version=1,
        text=sanitized_or_candidate_evidence,
    ),
    owner="repair-worker",
)
```

`inspection.decision` is a `Decision` enum. `inspection.candidate` is cleaned text or `None`; it is excluded from repr, transient and expires. `inspection.view()` produces the redacted API view. Reasons are constrained codes, not model prose. **Hold the job** when candidate is None or decision is not ALLOW/SANITIZE. Missing Gemma, malformed spans, large context or scanner failure produces a held result; do not fall back to raw evidence.

`local-preview` permits local inspection/preview only, not external coding-client release. Trusted worker code may use an ALLOW/SANITIZE candidate for the enrolled local Gemma workflow. For actual client/network delivery, register a permitted receiver in trusted startup code and use the bound one-use controller below. Never treat a preview as proof of transmission filtering.

```python
async def deliver(
    request_id: str,
    *,
    owner: str,
    version: int,
    destination: str,
) -> dict: ...

# Trusted startup enrolment, no API accepts arbitrary receiver URLs:
app = create_app(settings, receivers={"configured-client": receiver})
# receiver is async def receiver(cleaned_text: str) -> None
```

Evaluate and deliver must use the same owner/version/destination and current policy. One receiver attempt per inspection; ambiguous failures require a fresh investigation/inspection rather than automatic resend. `GuardError.code` and `.status` are safe, fixed metadata.

The first contextual request budget is 2 KiB of serialised task/text, to avoid silent truncation in the 4K model context. The outer scanner accepts up to 32 KiB. Supply bounded relevant excerpts; do not trim private content silently to force an ALLOW result.

### Your synchronous GuardPort

Mac 1 supplies `devguard.guard.repair_bridge.RepairGuardBridge`:

```python
from devguard.guard.repair_bridge import RepairGuardBridge
from devguard.repair.contracts import RepairError

# Inside async application startup, after the branches are combined:
guard_port = RepairGuardBridge(
    app.state.guard, asyncio.get_running_loop(), RepairError, timeout=25,
)
# Worker-thread signature:
# guard_port.sanitize(text: str, *, purpose: str) -> str
```

Accepted purposes are exactly `snapshot_source`, `test_evidence`, `tool_result` and `patch_export`. It returns an ALLOW/SANITIZE candidate after the guard's final scanner check, removes its transient preview record, and raises fixed-code `RepairError` on unavailable/held/oversize/timeout checks. Timeout cancels the scheduled inspection. Calling it from the app loop is rejected to avoid deadlock. No second model client or event loop is created.

This port approves local worker input; it does not transmit to an external receiver. Preserve your existing byte-for-byte equality requirement for source snapshots and patch exports. A changed source/patch stays held; sanitized diagnostic text may be used locally. Three cross-thread tests cover cleaned output, unavailable/scope holds and cancellation; actual Gemma classification remains pending.

## Operator-auth dependency

```python
from fastapi import Depends

operator_auth = app.state.operator_auth

@router.post("/patches/{candidate_id}/apply")
async def apply_candidate(candidate_id: str, principal: str = Depends(operator_auth)):
    # principal == "operator"; still perform base-hash/scope/approval checks.
    ...
```

Actual dependency signature:

```python
async def authenticate(
    credentials: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
) -> str: ...
```

Use it through FastAPI `Depends`, not as a worker function or tool available to the model. It returns `"operator"` or raises the app's handled 401 exception. It never returns the secret token. An optional distinct adapter credential cannot satisfy this dependency. Operator auth does not replace explicit apply approval, stale/base checks or patch-scope validation.

Your `create_repair_router(service, require_operator)` accepts a FastAPI dependency callable. Pass `app.state.operator_auth`; FastAPI supports this async dependency on synchronous routes, so a second synchronous token validator is unnecessary. Mac 1 owns mounting it once and supervising the worker lifecycle when the branches are integrated.

```python
app.include_router(create_repair_router(service, app.state.operator_auth))
```

Do not call blocking `sanitize()` or `next_action()` on the app event loop. Keep them in your existing worker thread. Auth is for HTTP routes, not a model tool or worker-held operator credential.

## Events and integration gates

`app.state.repair_event_sink(event) -> int` is now the synchronous, thread-safe constrained adapter for Mac 2's event dictionary. Pass it as `RepairService(event_sink=...)`. It reconstructs canonical metadata and discards supplied prose/raw payloads/evidence. The CLI persists it in private `.devguard/audit.sqlite3` with 5,000-event retention; test/embed `create_app()` defaults to in-memory unless an audit store is supplied. Storage failures raise fixed `AuditUnavailable`; Mac 2's existing sink handler holds/pauses work.

`create_app(settings, ..., repair_factory=async_factory)` now owns lifecycle initialization and mounts your router once. The trusted async factory receives `app` and returns your actual `RepairService`, reusing the exported model/guard/auth/audit ports. The supplied optional demo factory registers only the cart manifest, verifies a pinned installed Docker image, requires the real model digest and starts paused. `POST /repair/initialize` can retry that same configuration after prerequisites become ready. No model-selected root or image is accepted. Model calls are canceled on shutdown, the worker is paused/joined and audit storage is closed afterward. Real Docker/model trials remain pending.

## Protected source reads

`ProjectFiles(root).read_text(relative_path) -> str` in `devguard.guard.paths` anchors the approved root using a file descriptor. Close it after the job. It rejects protected names, traversal, symlink escape, nonregular and oversized files. Creation of an approved root is trusted operator work; no model-selected roots. Raw returned text must still pass privacy inspection before a model/tool delivery.
