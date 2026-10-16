# Mac 1 guard and startup handoff — 16 October 2026

Branch: `codex/mac1-guard-readiness`, based on `main` at `53ad6b9`, including Mac 2 PR #10. This branch changes only Mac 1 integration/model/guard files, their tests and shared status documents. Mac 2 continues to own the worker, client adapter and final repair/demo evidence.

## Requested fixes

- `RepairGuardBridge.sanitize(text, *, purpose)` retains the same signature. Its four enrolled purposes use sensitivity inspection with `task=None`: trusted manifests/named tools already choose relevant repair evidence. The model must not conversationally trim reproduction source, test output or diffs. Prompt/clipboard requests with an explicit task still receive relevance filtering.
- Credential detection, local semantic confidentiality/personal-data checks, exact quote validation, final scanning and held/error behavior remain active. No fixture is approved specially. The worker still requires byte equality for source snapshots/patch exports and rejects unsafe changes.
- The contextual model proposes exact contiguous quotes; trusted code computes Unicode spans. Missing, ambiguous, overlapping or contradictory quotes hold. This replaces model-generated character offsets, which failed to remove complete confidential facts in the initial synthetic trial.
- The trusted demo factory supplies readiness from the actual priority queue, private durable audit store, app-supervised worker lifecycle and an inspected pinned Docker image with a fixed project manifest. HTTP/model requests cannot enable these capabilities or select roots/images.
- App shutdown pauses work and calls/checks `service.shutdown(30)` off the event loop. If the first bounded drain cannot stop an active model call, model closure cancels inference and a second drain must acknowledge worker termination before guard/audit close. Missing acknowledgement raises a fixed shutdown error.
- Routes remain mounted once. Clipboard capture starts OFF; no native clipboard access was enabled during these checks.

## Runtime and checks

Mac 1: Apple M4 / 16 GiB, Python 3.11.14, Ollama 0.40.4. Exact model `gemma4:e4b-it-q4_K_M`, installed digest:

```text
dc35e8d9c6061baa6f0fa870975ab6932e2542b579b13ea0f199fa4bb7300c9c
```

Shared settings: context 4,096; output 512 for privacy / 1,024 for tools; temperature 0; `think=false`; one bounded priority queue. The repair adapter pins the inspected digest and checks it before each model action. Ollama reported the `llamacpp` runner and GPU execution. A post-trial memory query reported 23% system memory free; this is a single sample, not peak RAM measurement.

- `.venv/bin/python -m pytest -q`: **171 passed**, one existing Starlette/HTTPX deprecation warning, with merged PR #10. Unit model/verifier ports are explicitly fake.
- Real native model multiply smoke: PASS; one tool call, actual result 703 used by the final response; 12.35 seconds on the earlier initial settings. Mac 2 independently records its own continuation probe.
- Real guard plus managed local reference receiver: four declared synthetic regression cases (benign, credential, confidential prose, unrelated context) delivered the inspected useful bytes; targeted sensitive/unrelated values were absent and debugging evidence remained. All four replay attempts were held. Measured elapsed times: 0.96, 1.31, 1.48 and 1.29 seconds. These are four examples, not a general accuracy benchmark or installed-client interception proof.
- Model download is complete. Docker engine 29.6.1 and the prepared verifier image are available on Mac 1. No further model or cloud GPU download is needed for the next trial.

## Mac 2 trial handoff

Use the existing startup command with **your own** actual image ID:

```sh
.venv/bin/python -m devguard --demo-image-id sha256:REPLACE_WITH_YOUR_ACTUAL_IMAGE_ID
```

It starts with capture OFF and repair PAUSED. Create the named `demo-cart` / `cart` incident, queue it, then use manual idle. The model/guard/auth/event interfaces are unchanged. `POST /api/v1/repair/initialize` retries only the trusted startup configuration.

A separate Mac 1 local experiment obtained a genuine Docker baseline FAIL → Gemma patch → independent PASS → READY_FOR_REVIEW in **38.24 seconds**, without applying the candidate. Original source and trusted-test hashes were unchanged during the run. It used a native tool conversation, explicit writable-file information, a finite ten-action/two-patch budget, and surfaced genuine server exceptions from the test client while retaining all business assertions. Those worker/test adjustments are **not included in this Mac 1 handoff branch** to avoid overwriting Mac 2's concurrent PR #10 work. Mac 2 should review them and rerun its final exact configuration before claiming that milestone for the merged build.

Earlier experiments stopped on invalid native history, a semantic guard hold, a denied non-writable edit, exhausted tool budget or failed independent verification. They are failures, not successes. No manual source repair, scripted successful result, model fallback or changed expected business result was used.

Useful findings for Mac 2: include `writable_files` in the initial task, retain native call/result history, allow room for the two bounded patch attempts plus checks/finish, and consider removing `raise_server_exceptions=False` from the test client so actual backend exceptions reach the guarded evidence rather than an opaque HTTP 500. Any verifier change needs both Mac owners' review.

Remaining gates: Mac 2's exact final repair/stale/cancel/disposable-apply trial; installed Codex interception and a productive restricted tool workflow; native opt-in clipboard copy/read/write trial; wider unseen privacy/repair evaluation. Windows QA catalogue entries remain UNRUN unless their exact scenario was actually executed; the four local reference cases are a separate experiment. No production or universal protection claim is made.
