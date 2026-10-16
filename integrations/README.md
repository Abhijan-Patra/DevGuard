# Local operator launchers

Run from the DevGuard repository root. The existing backend creates/reuses the private `.devguard/session-token`; the local dashboard launcher reads it through the same trusted helper and keeps it only in dashboard session memory. It does not print it, send it to a model, or enable clipboard capture.

Mac 2 currently has an SSH forward to Mac 1 occupying port 8765. Keep that tunnel running and launch the local Mac 2 backend on 8766:

```sh
.venv/bin/python -m devguard --port 8766 --demo-image-id sha256:YOUR_ACTUAL_LOCAL_IMAGE_ID
DEVGUARD_LOCAL_API_PORT=8766 .venv/bin/python -m streamlit run integrations/local_dashboard.py
```

The second command is run in another terminal. Open `http://127.0.0.1:8501`; it starts in Live Mode, using `http://127.0.0.1:8766/api/v1`. The environment setting accepts only a local numeric port. The ordinary UI can still be launched separately in visibly labeled fixture mode; this launcher does not substitute fixtures when the API holds a request.

For a disposable, repeatable real trial without changing the repository's cart source or trusted tests:

```sh
.venv/bin/python -m devguard.repair.demo_trial --image-id sha256:YOUR_ACTUAL_LOCAL_IMAGE_ID
```

Add `--exercise-apply` to exercise explicit operator application, repeat idempotency and an actual post-apply Docker check **only on the disposable public demo copy**. A held guard or failed independent check remains a failure/hold, with no scripted patch. The trial verifies shutdown and reopens its temporary durable audit before cleanup. It uses the real app/operator routes through an in-process ASGI client; it does not establish installed Codex interception or browser/native clipboard coverage.

The coding-client prototype and its coverage limits remain documented in [codex/README.md](codex/README.md).
