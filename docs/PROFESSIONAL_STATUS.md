# Current implementation and measured scope

21 October 2026. All execution and verification below used this one laptop. The former four-machine handoff is no longer needed.

## Implemented in this finishing branch

| Capability | Current behavior | Verification |
|---|---|---|
| Dedicated browser UI | Responsive dark/light workspace; eight feature views; no Streamlit widget shell | Browser visual review; served-asset/header test; JavaScript syntax check |
| Local browser enrollment | Explicit same-origin connect; HttpOnly/SameSite Strict expiring cookie; no bearer in JavaScript/URLs | Local/remote/origin/header/disconnect boundary tests |
| Text context gate | Rules + pinned Gemma + bounded exact-span validation + final output scan | Real synthetic delivery and benchmark; guard boundary suite |
| Managed source access | Exact registered source manifest; descriptor-anchored reads; source hash checked on **all** delivery routes | Actual API integration tests, including generic-route bypass rejection |
| Local composer | Real approved receiver bytes, replay rejection, ten-minute memory-only retention; explicit copy/clear | [Real delivery metadata](evidence/professional-delivery.json) |
| Opt-in native clipboard | Required text capture, no existing-copy read, versions, stale refusal, own-write suppression and disable cleanup | Isolated native pasteboard: **12/12**, 7.971 s copy-to-finding; general clipboard not accessed in this finishing run |
| Backend investigation | Genuine Gemma tools and candidate patch, immutable independent Docker verification | [Real single-laptop repair](evidence/professional-repair.json): **45.96 s**, baseline FAIL, independent PASS, disposable apply, idempotent repeat, post-apply PASS |
| Original source review | Explicit approval, expected hashes, conflict refusal, cancellation and reject | Existing and expanded integration tests; real disposable trial |
| Reviewed rollback | Reverse atomic apply; refuses concurrent edits; idempotent; original bytes retained only in session | [Real Docker/API rollback trial](evidence/professional-rollback.json): modified-source refusal, exact restore, idempotent repeat; post-apply PASS, restored original bug FAIL |
| Project enrollment | Reviewed CLI JSON manifests; up to eight projects; fixed files/tests/images; no arbitrary HTTP enrollment | Manifest scope validation tests; launcher enrolls disposable demo copy |
| Saved-file monitoring | Opt-in exact manifests, debounce, dedupe, queues while paused, lifecycle shutdown | Integration tests and real saved-file → queued → Gemma → independent PASS trial |
| Quiet-time admission | Opt-in based on foreground queue timestamps; manual pause disables automation | Real 15-second admission trial plus integration checks; **not** OS idle detection |
| Audit and export | Redacted SQLite metadata, pagination/filter, explicit loaded-record export | Existing storage and integration suite; no raw input persisted |
| Single-laptop startup | Starts dependencies if stopped, verifies exact model/image, detached owned process, safe stop | Live local start/health; process identity and graceful stop tested during development |

## Automated verification

The integrated local suite passed **238 tests**, with one existing upstream Starlette/HTTPX deprecation warning. `pip check` reports no broken requirements. This is not a model-accuracy score; the suite includes declared doubles. A wheel build completed with the workspace assets included. Remote GitHub Actions checks also passed for this finishing branch and PR #21.

## Model evaluation limitations

[Five actual catalogue inspections](evidence/professional-privacy.json) were run against the real pinned Gemma on synthetic input, mapped explicitly to local-preview (no external delivery). The original expected outcomes were preserved:

- P01: SANITIZE/CREDENTIAL, expected decision and reasons matched.
- P02: returned SANITIZE/PERSONAL_DATA for a harmless identifier; expected ALLOW. **False positive.**
- P03: returned SANITIZE/CONFIDENTIAL; expected REVIEW. **Decision mismatch.** This measurement alone does not establish that all confidential facts were removed.
- P04: SANITIZE/CREDENTIAL/PERSONAL_DATA; expected decision and reasons matched.
- P05: BLOCK; expected CREDENTIAL plus PROMPT_INJECTION, but only CREDENTIAL was reported. **Reason-code mismatch.**

These are calibration results, not an unseen accuracy benchmark or five passing cases. The older combined catalogue registry is left unchanged; remaining catalogue cases are not retrospectively marked passed. No fabricated repair, fixture-specific classifier rule or successful fallback model was added.

## Remaining integration gates

- Existing native Codex hooks are restrictive and **unverified** as a productive installed-client integration. The supported productive scope here is the explicit local context gate/managed source/composer workflow. Automatic context, attachments, alternative tools and client transcripts are outside it.
- Native Windows capture is not implemented. This delivery targets this Mac; no second laptop is assumed.
- Quiet-time admission does not infer actual OS/user idle. Sleep suspends execution.
- Generic Python projects require explicit small source manifests, separately reviewed pytest checks and a prepared image. This is not an every-language/every-bug production recovery system.
- Rollback/candidates are session-only. Restart clears them; persisted audit metadata cannot reconstruct them. Single-file replacement still has a narrow race against unrelated editors after the final hash check.
- The redesigned public read-only tour is deployed at https://devguard-demo.onrender.com; HTTP 200 and the actual new browser view were verified. Device controls stay disabled there. The real workspace is local at `http://127.0.0.1:8765/app`.

The implementation is a working scoped local agent, with the above gates stated explicitly. Perfect detection, universal interception and production certification are not claimed.
