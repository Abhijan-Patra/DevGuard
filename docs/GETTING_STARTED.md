# Getting started: Mac 1 guard and clipboard service

Ollama is already installed on the first Mac. Gemma downloads separately; implementation and control tests do not depend on waiting for it. Runtime endpoints hold requests when contextual analysis is unavailable.

## Install and run

Python 3.11 is available on the first Mac. The backend supports Python 3.11 or later:

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install -e '.[dev,clipboard]'
brew install gitleaks
.venv/bin/python -m pytest -q
.venv/bin/python -m devguard
```

The clipboard extra installs the macOS bridge only on macOS. Gitleaks is an external executable. For the captured tested package versions, install `requirements.lock.txt` then install the editable project with `--no-deps`; PyObjC pins are macOS-only. Windows UI members need neither native capture nor the model.

The server binds to `127.0.0.1:8765`. The CLI creates `.devguard/session-token` with private permissions if no environment token is supplied. It prints the path, never the token. Audit metadata is kept in private `.devguard/audit.sqlite3`, with 5,000-event retention; raw input/previews never persist. The capture service always starts OFF.

## Explicit clipboard controls

Status checks do not read clipboard text:

```sh
.venv/bin/python -m devguard.clipboard.cli status
```

When the local operator chooses to inspect future copied text, explicitly enable:

```sh
.venv/bin/python -m devguard.clipboard.cli enable --consent --task "Diagnose the login exception"
```

The existing clipboard at enable time is not read. Future text changes run fast detectors and, where needed, local contextual analysis. Binary/oversized/empty copies are skipped visibly. Missing or invalid analysis stays REVIEW with no cleaned-copy release. Capture does not intercept every unrelated app paste.

Only after an actual completed inspection offers a candidate:

```sh
.venv/bin/python -m devguard.clipboard.cli copy-cleaned
```

This checks the inspected version and native change counter, writes explicitly and suppresses self-trigger loops. NSPasteboard cannot guarantee a global atomic write across all apps; a lost/raced write is not retried automatically.

Disable and clear transient state:

```sh
.venv/bin/python -m devguard.clipboard.cli disable
```

The control CLI never prints raw clipboard text. Native capture/copy has not been exercised against the user's clipboard during development; only import/availability and synthetic-adapter tests have run.

## Model download and later smoke test

The selected package remains Gemma 4 E4B with explicit Q4 quantisation:

```sh
ollama pull gemma4:e4b-it-q4_K_M
```

The first Mac's download is already running. The generic E4B tag initially chose a larger backend-dependent package, so that attempt was stopped. Existing unrelated models remain untouched. No paid cloud service is needed.

After download completes, the real trial command is:

```sh
.venv/bin/python -m devguard.models.smoke
```

It validates a native model tool call, executes a bounded multiplication function and checks the model uses the real result. Exit 0 is success; exit 2 means server/model unavailable; exit 1 is a failed real trial. This is not a privacy benchmark or repair proof, and no model success is fabricated while downloading.

## Interfaces and scope

See [API contract](API_CONTRACT.md) and [Mac 1 implementation handoff](MAC_1_IMPLEMENTATION.md). Operator tokens can control local capture; an optional distinct `DEVGUARD_ADAPTER_TOKEN` can evaluate/deliver its own requests only. Do not copy operator credentials into model context or a coding-client hook.

`local-preview` has no outgoing receiver. Real client delivery requires trusted code enrolment by Mac 2, plus that adapter's actual end-to-end coverage tests. Private inputs must not be sent through an unrelated unguarded tool while relying on this service for protection.

Mac 2 repair routes and the Windows dashboard are integrated. Read [integrated setup](INTEGRATION_STATUS.md) for the optional UI installation, pinned Docker demo configuration, actual checks and pending live trials. Repair uses source/diffs/logs/API probes/tests; clipboard capture remains required.
