# Integrated backend and dashboard status

16 October 2026. Current combined Mac 1/dashboard handoff: `codex/mac1-windows1-finish`, including PR #13, PR #14 and main through PR #12. See [completion evidence](MAC_1_WINDOWS_1_COMPLETION.md) for digest enforcement, native clipboard checks and the real live-dashboard trial. The [earlier guard/readiness handoff](MAC_1_READINESS_HANDOFF.md) records the startup changes and Mac 2 repair coordination.

## Implemented together

- Windows 1's existing Streamlit dashboard now uses port 8765 and actual backend request/response shapes. Coverage envelopes, clipboard consent/version fields, delivery bindings and patch approval/candidate/base/idempotency fields are aligned.
- Live mode never falls back to fixture privacy results. Switching mode, credentials or backend clears the previous result. Fixture actions retain their own session state, and fixture evaluation displays declared synthetic data rather than classifying or echoing arbitrary typed text.
- The live HTTP display client uses loopback enrolment, no proxy environment or redirects, fixed safe transport errors and no fallback inference. Model-unavailable readiness is distinct from API connectivity. Policy holds are distinct from authentication errors.
- The CLI uses private `.devguard/audit.sqlite3` SQLite storage, with at most 5,000 events. Metadata survives restart; clipboard/candidate/repair work does not. Worker and API operations share a lock. Supplied repair summaries, raw fields, evidence text and model prose are discarded before persistence.
- Mac 2's routes are mounted once with Mac 1's operator dependency. Unconfigured repair returns an explicit unavailable state; it does not launch a fake worker. Incident listing adapts the existing service metadata for the dashboard.
- Trusted startup can opt into the existing cart demo with a pinned, already-built Docker image. It shares the actual model, guard and audit instances, starts paused and shuts down cooperatively. Missing Gemma, image or Docker holds initialization while leaving privacy/status services running.
- Required opt-in text clipboard capture remains OFF at startup. Explicit local consent is required; screenshots and recordings are not used.

## Checks

The combined suite passes **198 tests**, with one upstream TestClient deprecation warning. `pip check` reports no broken dependencies. Streamlit 1.66.0 is installed in the local virtualenv; optional UI versions are captured in `requirements-ui.lock.txt`.

A live API check returned REVIEW/CREDENTIAL/MODEL_UNAVAILABLE with no preview for declared synthetic input; the value was absent from audit responses. The live server reported durable audit storage, capture OFF and repair NOT_CONFIGURED; its database is mode 0600 and the dashboard health endpoint returned 200. The synthetic event remained present after a real backend process restart, with capture still OFF.

Checks include real SQLite reopen/persistence and concurrent writes, storage permission/symlink/hardlink refusal, candidate revocation on audit failure, actual FastAPI/display-client contract checks and Streamlit element-tree rendering of all five views in fixture and live modes. The live-mode test verifies an unavailable contextual model produces REVIEW with no preview and never displays the fixture decision.

A combined test exercises the existing repair service, cross-thread guard port, audit sink, API and UI client with explicitly fake model/verifier ports. It verifies originals stay unchanged before approval and both candidate/base fields are required. This validates integration boundaries only; it is not a real model repair or Docker verification result.

## Start the actual services

Backend:

```sh
.venv/bin/python -m devguard
```

Dashboard:

```sh
.venv/bin/python -m pip install -e '.[ui]'
.venv/bin/python -m streamlit run devguard/ui/app.py
```

The tracked Streamlit configuration binds only `127.0.0.1:8501` and disables usage telemetry. Keep it local because operator credentials and native clipboard controls belong on the capture Mac. Fixture mode is the default. Live mode uses `http://127.0.0.1:8765/api/v1` and the local operator token. Do not paste that token into a development assistant or GitHub.

For pinned versions, install `requirements.lock.txt` then optional `requirements-ui.lock.txt`, followed by `pip install --no-deps -e .`.

## Enable real demo repair after prerequisites are ready

1. Confirm the exact Gemma package is installed. Download and native smoke have completed on both Macs; see the handoff for the measured digest.
2. Start the Docker engine. Build the existing scoped demo runner with `python demo/backend/build_runner.py` and obtain its actual `docker image inspect devguard-runner:mac2 --format '{{.Id}}'` value.
3. Start the backend with `--demo-image-id` and that actual `sha256:` ID. It never pulls/builds an image automatically. Only the declared cart source manifest is registered; tests/policy remain outside model write scope.
4. If startup was held while prerequisites were unavailable, the authenticated `POST /api/v1/repair/initialize` retries the same trusted configuration. It cannot accept a new root/image through HTTP.
5. Create a named cart incident, queue it and explicitly call the manual idle route. Inspect the real baseline, native model actions, independent verification and reviewed diff. Apply requires explicit approval and both inspected hashes.

The local Docker engine and prepared image are available. Real Gemma/reference-receiver checks passed on four synthetic examples. A separate local repair experiment passed; Mac 2 is completing the final exact repair/demo evidence as described in the handoff. Controlled synthetic native clipboard read/write passed on both a private named board and the system board after explicit consent; capture is now OFF. Installed-client interception remains pending. Saved-file monitor code exists but is not yet supervised by this app; this build uses explicit named incident/idle actions. No production deployment or recovery claim is made.

The shared model client now checks the pinned package digest after queue admission and before inference. The dashboard requires the actual live status envelope and stops on incompatible mock servers; use labelled Fixture Mode for rehearsal. The real live-dashboard check used the actual local API and Gemma with an in-process reference receiver, not the standalone mock server. See the completion evidence for exact scope and timings.
