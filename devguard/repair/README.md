# Mac 2 repair implementation and measured handoff

The local Gemma repair loop reproduces the declared cart defect, produces a genuine model patch, passes independent Docker checks and returns an operator-reviewable candidate. Disposable application, repeated application and stale-source refusal were exercised through the actual API. These are small synthetic demonstrations, not a general repair benchmark.

## Actual verification — 16 October 2026

Host: Apple M4 Air / 16 GB; Python 3.12.14; Docker Desktop 4.95.0 / engine 29.8.2; Ollama 0.40.5; Gitleaks 8.30.1; PyObjC Cocoa 12.2.2; Streamlit 1.66.0. Exact model: `gemma4:e4b-it-q4_K_M`, digest `dc35e8d9c6061baa6f0fa870975ab6932e2542b579b13ea0f199fa4bb7300c9c`. Shared settings: context 4096, privacy/tool output 512/1024, temperature 0, thinking off.

| Check | Measured result |
|---|---|
| Integrated suite after main `1099a86` + Mac 2 | **209 passed**, one existing Starlette/HTTPX deprecation warning; `pip check` clean. Fake unit-test ports are not model-accuracy evidence. |
| Native continuation probe | Two genuine calls consumed fresh random host-generated integers; result 75, 7.14 s. No runtime answer lookup. |
| Real disposable API apply on integrated code | Baseline FAIL → native Gemma investigation/patch → independent Docker PASS → READY_FOR_REVIEW → operator-approved disposable APPLIED → idempotent repeat → post-apply Docker PASS. **46.07 s**, 28 audit records survived reopening, worker stopped, original source/tests unchanged. [Metadata](verification/mac2-disposable-apply.json). |
| Real queued cancellation + stale apply | Queued cancel created no candidate. A genuine candidate passed; after a concurrent disposable edit, apply returned **409 STALE_SOURCE**, preserved the edit and marked the run OBSOLETE. **42.19 s**, 25 audit records survived reopening, worker stopped, original source/tests unchanged. [Metadata](verification/mac2-stale-cancel.json). |
| Actual HTTP backend + dashboard | Local backend generated a PASS candidate; the live repair view rendered its actual diff with zero exceptions. Candidate remained unapplied. State is transient after restart. |
| Consented Mac 2 system clipboard test | **HELD/REVIEW**, final scanner POLICY_BLOCK; cleaned-copy was not exercised. Capture disabled and confirmed OFF. [Metadata](verification/mac2-system-clipboard-held.json). Mac 1 separately measured a passing input in [its evidence](../../docs/MAC_1_WINDOWS_1_COMPLETION.md). |

Earlier repair attempts stopped on privacy holds. A later stale-trial attempt stopped on an invalid native model action after three tools; no patch was applied ([failure metadata](verification/mac2-format-hold.json)). One bounded response-format retry was then added and unit-checked; subsequent real successful runs needed **zero** such retries. Failures remain failures. No guard bypass, manual source fix or changed business assertion produced these results.

The trusted-test transport adjustment is `TestClient(app)` instead of `raise_server_exceptions=False`, exposing actual backend exceptions in guarded evidence. Inputs, expected responses and business assertions are unchanged. Both Mac owners must review before merge. Tests remain outside the model-writable snapshot.

## Implemented boundaries

- Explicit source manifests include saved edits, hashes, limits and private disposable snapshots. Traversal, symlink/hardlink escapes and protected paths are rejected.
- Typed tools list/read approved files, run enrolled checks, propose one-file sandbox replacements and finish. The task declares writable files; native call/result history omits arbitrary model prose and hidden reasoning.
- Ten actions, two patches and a 180-second investigation budget, with finite model/verifier calls. At most one transport-format retry consumes that same budget. Typed-policy/path denials do not retry as format errors.
- Prepared Docker image by immutable ID; no runtime pull/install, no network, non-root user, dropped capabilities, read-only root/tests and bounded resources/output/time. No host shell fallback or Docker socket inside the target.
- Genuine failing baseline and independent final PASS required. Every model-bound result and exported diff passes the guard. Source/export bytes must remain exact; cleaned diagnostic evidence may be used locally.
- The model edits approved snapshot source only. Original application requires operator approval, candidate/base hashes, scope checks and idempotency. Concurrent edits invalidate candidates. Single-file replacement is best-effort against unrelated editors; no multi-file transaction is claimed.
- One supervised worker, queued cancellation, pause/manual idle, bounded retained state, saved-file monitor component and durable redacted metadata. Automatic OS-idle scheduling, general project enrollment and production probes remain unfinished. Sleeping laptops cannot repair overnight.

## Reproduce from the repository root

Install pinned backend dependencies with Python 3.12 and start Docker/Ollama. The measured local ARM64 image was `sha256:c74d2d570e55537d0b57d10c8c079834dbacf14b10a7e79768edebf6733aa6c7`; other hosts build/inspect their own image.

```sh
.venv/bin/python -m pytest tests -q
.venv/bin/python -m pip check
.venv/bin/ruff check --isolated --select E4,E7,E9,F,I devguard/agent devguard/monitor devguard/repair devguard/api/repair_routes.py integrations/codex integrations/local_dashboard.py demo/backend trusted_tests tests/backend
.venv/bin/python demo/backend/build_runner.py
docker image inspect devguard-runner:mac2 --format '{{.Id}}'
.venv/bin/python -m devguard.agent.tool_smoke
```

Substitute the actual image ID below. The trial uses real model/guard/API/Docker ports on a disposable **public demo copy**; it never applies to the repository. Report files are new private 0600 files, refusing overwrite. Keep full local reports outside Git.

```sh
.venv/bin/python -m devguard.repair.demo_trial --image-id sha256:ACTUAL_IMAGE_ID --exercise-apply --queued-cancel --report-file /tmp/devguard-apply-new.json
.venv/bin/python -m devguard.repair.demo_trial --image-id sha256:ACTUAL_IMAGE_ID --exercise-stale --queued-cancel --report-file /tmp/devguard-stale-new.json
```

Persistent local demo (starts paused, capture OFF):

```sh
.venv/bin/python -m devguard --port 8766 --demo-image-id sha256:ACTUAL_IMAGE_ID
DEVGUARD_LOCAL_API_PORT=8766 .venv/bin/python -m streamlit run integrations/local_dashboard.py
```

8766 is a Mac 2 override preserving the existing SSH tunnel on 8765. The launcher reads the existing private local token into dashboard session memory without displaying it or giving it to the model. Use operator incident `demo-cart` / `cart`, investigate, then manual idle through the operator API. The mock server is rehearsal data, not actual execution. A healthy baseline correctly produces no repair.

## Integration and remaining coverage

`build_mac1_binding()` reuses the actual model queue, `RepairGuardBridge`, operator auth and durable event sink. Worker calls run off the app loop. The trusted factory returns the service; the app mounts the router once and supervises shutdown before guard/audit closure. Readiness derives from actual priority queue, durable audit, lifecycle and inspected verifier. HTTP/model inputs cannot enable it or choose roots/images. See [Mac 1 interfaces](../../docs/MAC_2_INTEGRATION.md) and [readiness handoff](../../docs/MAC_1_READINESS_HANDOFF.md).

Foreground privacy overtakes waiting background calls; active inference is not preempted. Concurrent latency has not been measured. Candidate/clipboard/source state is transient; restart does not resume/apply work.

The [Codex adapter](../../integrations/codex/README.md) remains a restrictive prototype: installed-client interception/productive restricted workflows are unverified. Clipboard observation cannot prevent arbitrary pastes; local preview is not outbound delivery. Mac 1 separately measured a managed local reference receiver. Universal interception, perfect detection, Windows native capture and production recovery are not claimed.
