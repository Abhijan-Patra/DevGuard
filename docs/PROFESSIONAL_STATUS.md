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

The integrated local suite passed **267 tests**, with one existing upstream Starlette/HTTPX deprecation warning. `pip check` reports no broken requirements. This is not a model-accuracy score; the suite includes declared doubles. A wheel build completed with the workspace assets included. The prior finishing branch passed remote GitHub Actions in PR #21. The current client/calibration branch records its own CI result separately.

## Privacy calibration and native client trials

The [earlier five-case baseline](evidence/professional-privacy.json) remains preserved: P02 false-positive redaction, P03 decision mismatch and P05 missing injection reason are still visible. The [corrected real-Gemma rerun](evidence/professional-privacy-calibrated.json) matches all five original decisions and required reasons without changing the catalogue. The fix distinguishes technical formats/public constants from personal data, requires review for confidential spans, and blocks/reports detected policy-override attempts. Generic credential baselines remain protected independently of provider example allowlists.

Eight additional declared synthetic variants were defined before their first run. That [first measurement](evidence/professional-privacy-variants-first.json) found a sentence-final email detector miss (V06). The detector was corrected with punctuation regression tests; the [rerun](evidence/professional-privacy-variants.json) matches all eight expectations. These are small calibration/regression sets, not an independent unseen accuracy estimate. P06/P07 in the older combined catalogue are not retrospectively marked passed by ordinary text inspection.

[Thirteen recorded native boundary checks](evidence/professional-native-clients.json) passed using installed bundled Codex CLI `0.163.0-alpha.10.2`, Claude Code `2.1.119`, MCP SDK `1.30.0` and the **real** pinned Gemma guard. Tests covered sensitive prompt hold, benign positive controls, clean managed reads, source credential redaction, traversal holds, native Codex shell denial, and unavailable-guard holds in both clients. Coding-provider transport was a **local synthetic protocol fixture**, not a cloud coding model; the receiver recorded marker-presence metadata. Codex hooks were reviewed/trusted in the native UI in an isolated home; no bypass flag or global config change was used. Claude was not signed in, so this is not signed-in cloud account evidence. See [setup and exact scope](CLIENT_INTEGRATION.md) and [reproduction harness](../evals/native_trials/README.md).

The productive external-client surface is now two stdio MCP tools: registered source listing and guarded source read. Source reads undergo the actual server-side scan/hash/one-use boundary before returning text. The scoped client credential cannot access operator, composer, clipboard or repair controls. Client profile generation is isolated and never preinstalls trust. Required opt-in native clipboard capture remains unchanged.

## Remaining integration gates

- Native CLI prompt/MCP paths have the recorded scoped checks above. Signed-in cloud-provider delivery, desktop/IDE variants, automatic context, attachments, alternative/hosted tools, transcripts and telemetry remain unverified. Skipped/crashed/timed-out hooks can fail open at the native layer; the managed server output gate enforces its own holds.
- Windows native text capture and platform boundaries are implemented for v0.3.0; see [Windows setup and measured gates](WINDOWS.md). Hardware/model and signed-in Windows coding-client trials remain separate from native CI.
- Quiet-time admission does not infer actual OS/user idle. Sleep suspends execution.
- Generic Python projects require explicit small source manifests, separately reviewed pytest checks and a prepared image. This is not an every-language/every-bug production recovery system.
- Rollback/candidates are session-only. Restart clears them; persisted audit metadata cannot reconstruct them. Single-file replacement still has a narrow race against unrelated editors after the final hash check.
- The redesigned public read-only tour is deployed at https://devguard-demo.onrender.com; HTTP 200 and the actual new browser view were verified. Device controls stay disabled there. The real workspace is local at `http://127.0.0.1:8765/app`.

The implementation is a working scoped local agent, with the above gates stated explicitly. Perfect detection, universal interception and production certification are not claimed.

The [post-calibration real repair rerun](evidence/professional-post-calibration-repair.json) again reached READY_FOR_REVIEW from a failing baseline, passed independent Docker verification and post-apply Docker checks on a disposable copy, preserved original repository/trusted test files, and acknowledged worker shutdown.


## Windows support — 22 October 2026

Windows native clipboard, private ACL storage, canonical NTFS source handles, atomic reviewed apply/rollback, an isolated PowerShell installer and graceful owned-process shutdown are implemented. The [Windows native/package matrix](https://github.com/Abhijan-Patra/DevGuard/actions/runs/39720529119) passed on Python 3.11/3.12, including actual synthetic clipboard, junction, hard-link, file-lock and lifecycle checks. Common repair tests use declared model/verifier doubles; this is not Windows model accuracy or real Windows Linux-container Docker evidence. The actual hosted OS was Windows Server 2025; physical Windows 11 performance, Windows ARM and signed-in coding-client delivery remain unverified. See [setup and scope](WINDOWS.md).

The clean installed Mac v0.3.0 package passed real sanitized delivery, Gemma-generated repair, independent Docker verification, disposable reviewed apply and rollback. The initial privacy hold remains recorded separately. General clipboard content was not read in those release trials.
