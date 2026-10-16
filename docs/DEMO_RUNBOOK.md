# DevGuard live demo runbook — 16 October 2026

Mac 2 continues the assigned Windows 2 QA/demo work. Present actual Live Mode only when the real backend is available. Fixture Mode is an explicitly labelled rehearsal. The mock server is not real Gemma execution and is rejected by the current live-contract check.

## Prepared Mac 2 setup

Open <http://127.0.0.1:8501>. The local launcher selects **Live Mode (FastAPI Backend)** and reads the existing private local operator token without displaying it. Backend: `http://127.0.0.1:8766/api/v1`. Port 8765 remains the existing SSH tunnel to Mac 1; do not replace that tunnel or copy another operator's token.

Keep the Mac awake and plugged in, Docker Engine running and Ollama available. The prepared repair candidate is transient: restarting the backend removes its run/candidate state. Audit metadata survives, but it cannot reconstruct or auto-apply a candidate. Do not restart a ready demo without time to rerun the genuine investigation.

If startup is required, run each command in a separate terminal from the repository root, substituting the actual inspected local image ID:

```sh
.venv/bin/python -m devguard --port 8766 --demo-image-id sha256:c74d2d570e55537d0b57d10c8c079834dbacf14b10a7e79768edebf6733aa6c7
DEVGUARD_LOCAL_API_PORT=8766 .venv/bin/python -m streamlit run integrations/local_dashboard.py
```

That image exists on the measured Mac 2; other machines build/inspect their own. Capture starts OFF and repair starts paused. Creating an incident/queued investigation and invoking manual idle are operator API actions, not a model power. See [repair commands](../devguard/repair/README.md).

## Three-minute presentation

1. **0:00–0:25 — Problem.** “Developers paste too much private context into coding assistants, and backend failures take time to investigate. DevGuard uses one local Gemma model to inspect supported text paths and investigate a bounded backend failure.” Show Live Mode and the actual model digest. Do not claim universal interception or broad accuracy.
2. **0:25–1:05 — Privacy Gate.** In Custom Input, set task `Debug the HTTP 500 at cart.py:17`, destination `local-preview`, and declared synthetic text `password=synthetic-native-fixture-710938; HTTP 500 at cart.py:17.` Evaluate. Show the actual decision/reasons/preview. An approved cleaned preview should omit the dummy password while retaining diagnostic facts; if held, show the hold honestly. Do not replace the decision with a fixture. `local-preview` does not deliver externally; the separate managed-local-receiver experiment has a measured receipt and replay hold in the evidence.
3. **1:05–1:25 — Native text workflow.** Show capture OFF and explain explicit opt-in, future-copy-only observation and version-checked cleaned copy. The isolated native test passed all 12 checks; the separate combined-email/api-key system test was HELD and cleaned-copy did not run. No fresh system clipboard trial is needed for this presentation. Never turn capture on silently or claim arbitrary paste prevention.
4. **1:25–2:35 — Backend repair.** Open **Repair & Patches**, select the real `demo-cart` incident and show READY_FOR_REVIEW, baseline FAIL, independent PASS, completed native tools and the actual unified diff. The actual cart uses `unit_amount` and `quantity`; there is no `price` field in the runtime fixture. Explain that Gemma inspected evidence and modified a snapshot while the verifier remained outside its write authority. Leave repository apply for a deliberate operator decision; the disposable approved/idempotent apply already passed in 46.07 seconds.
5. **2:35–3:00 — Evidence and boundaries.** Show the real stale receipt: 409 STALE_SOURCE, developer edit preserved, run OBSOLETE; queued cancellation created no candidate. End with local Gemma, MIT application code, a public repository, and the measured scope. Automatic OS-idle scheduling and installed Codex interception remain unfinished; laptop sleep stops work.

## Failure branches

- Backend unavailable or incompatible: show the error, restore the actual backend, or switch visibly to Fixture Mode. Do not present the mock server as live inference.
- Privacy REVIEW/BLOCK/timeout: demonstrate that the request remains held. The user may revise input; no hard-policy override exists.
- Repair BLOCKED/UNRESOLVED: keep its reason and evidence. Do not paste a known repair into the runtime or weaken checks.
- Applied/healthy demo: a healthy baseline correctly produces no candidate. Use the disposable trial below for another genuine run rather than resetting user edits.
- Stale apply: preserve the concurrent edit; investigate a fresh snapshot. Never reset or force the old candidate.

## Repeatable measured commands

```sh
.venv/bin/python -m devguard.repair.demo_trial --image-id sha256:c74d2d570e55537d0b57d10c8c079834dbacf14b10a7e79768edebf6733aa6c7 --exercise-apply --queued-cancel --report-file /tmp/devguard-demo-apply-new.json
.venv/bin/python -m devguard.repair.demo_trial --image-id sha256:c74d2d570e55537d0b57d10c8c079834dbacf14b10a7e79768edebf6733aa6c7 --exercise-stale --queued-cancel --report-file /tmp/devguard-demo-stale-new.json
.venv/bin/python -m devguard.clipboard.smoke
.venv/bin/python -m devguard.ui.smoke
```

The first two use disposable public copies; they never apply to the repository. The default clipboard smoke uses an isolated named board and never touches the general clipboard. Do not add its optional system-clipboard flag without fresh explicit consent. Full local reports stay private; Git contains bounded metadata only.

See [measured evaluation](EVALUATION.md), [repair evidence](../devguard/repair/README.md) and [submission text](SUBMISSION_FINAL.md). Keep local tokens/audit databases/model weights/snapshots out of screenshots, recordings, Git and messages.
