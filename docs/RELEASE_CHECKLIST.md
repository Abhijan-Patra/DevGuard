# Public preview release verification

Version 0.2.1, 21 October 2026. This checklist distinguishes package/CI checks from actual local model/device results. Passing checks are finite evidence, not a guarantee that every installation or model answer will succeed.

## Required release gates

- Full regression suite, `pip check`, JavaScript syntax and source/doc consistency checks.
- Wheel and source distribution built from the reviewed commit; version/tag match.
- Clean, non-editable wheel installation outside the checkout on macOS/Linux with Python 3.11/3.12. API/static assets, explicit browser pairing, unauthenticated denial, capture/watchers OFF, and held/approved privacy contract must work without checkout files.
- Packaged public demo and independent oracle match reviewed source; Docker build context has exactly the two intended public files.
- Separate real pinned Gemma/Gitleaks/Docker trial on an Apple silicon Mac: sanitized delivery, genuine verified repair, review before apply, disposable apply, rollback and graceful managed stop. Never enable general clipboard capture in release automation.
- Review artifacts: no `.devguard`, tokens, raw logs, databases, private inputs, snapshots or weights. Publish wheel, source archive, tested runtime constraints and SHA256SUMS.
- README/install/support/security docs link to the actual main branch and release. The public tour stays read-only.

The tag-triggered [release workflow](../.github/workflows/release.yml) requires the reusable [verification workflow](../.github/workflows/ci.yml) before publishing. Review CI and the local evidence before pushing a version tag. The release title explicitly identifies the preview; no binary signing/notarization or desktop auto-updater is provided.

## Verifier compatibility follow-up

[Post-publication 0.2.0 holds](evidence/release-published-v0.2.0-holds.json) retain both failed trials, including the diagnostic BASELINE_UNAVAILABLE result before model investigation. Historical OCI-index tag/ID lookup was inconsistent in this Docker environment; no Docker engine root cause is claimed. Version 0.2.1 prepares a single-platform verifier under a tag derived from its public inputs/profile rather than reusing the historical tag. The [0.2.1 installed real workflow](evidence/release-wheel-live-v0.2.1.json) passed failing baseline, real generated repair, independent verification, reviewed disposable apply and rollback. Failed release trials now persist metadata without exception payloads.

## Local measured evidence

[Clean installed wheel smoke](evidence/release-wheel-smoke.json) and [real installed Gemma/Docker workflow](evidence/release-wheel-live.json) record synthetic, isolated trials. The latter uses a temporary canonical workspace, preserves the packaged independent oracle, and stops only its owned backend. It does not access the user's general clipboard or alter their project.

The [fresh source installation](evidence/release-source-install.json) also passed the documented installer, dependency check, read-only doctor and privacy-only start/status/stop commands from an extracted source archive. The local regression suite passed 283 tests; the release CI remains authoritative for its own matrix results.

The [sensitive clipboard trial](evidence/clipboard-sensitive-preview.json) separately covers real Gemma/Gitleaks with a private named NSPasteboard, placeholder display, explicit native cleaned-copy and held-copy refusal. It is not a broad accuracy benchmark.

Reproduce package checks with a fresh virtualenv, installing the built wheel and then running its interpreter with `-I scripts/release_smoke.py`. Add `--live` only on a prepared machine: it exercises real model/Docker work and explicitly applies/rolls back **its own disposable demo**. This is not a fixture success path; a failed or held repair fails the release trial.

## Remaining limits

Only macOS has a native clipboard adapter. CI can validate package/API behavior on Linux but does not establish Linux GPU/model performance or native capture. Python 3.13 is accepted by metadata but has not been included in the release matrix. Signed-in cloud coding-client delivery and arbitrary external tools are outside the recorded synthetic provider tests. Model accuracy, sandbox resistance and recovery have no production certification or guarantee. Review all enrolled source/test scope and candidate changes.
