# DevGuard

**A local Gemma-powered privacy guard and backend repair agent for AI-assisted development.**

Status: privacy/clipboard APIs, dashboard and Mac 2 repair routes are integrated. Capture starts OFF. The Mac 1 guard/readiness handoff passes 171 tests with merged PR #10, and four real Gemma synthetic cases passed through a managed local reference receiver. Mac 2 owns the final repair/demo and installed-client proof. See [current handoff](docs/MAC_1_READINESS_HANDOFF.md) and [integration status](docs/INTEGRATION_STATUS.md).

DevGuard inspects supported prompts, file access, tool results and copied text; it also investigates reproducible backend failures and prepares independently tested patches in a disposable workspace. Clipboard capture is a required, opt-in feature. Bug diagnosis uses source, structured logs, diffs, named API probes and tests; it does not depend on screenshots or screen recordings.

## Decisions

- **One model:** Gemma 4 E4B through Ollama, using the explicit local Q4 tag `gemma4:e4b-it-q4_K_M`. Different task prompts share one model and inference queue.
- **Priority:** privacy and clipboard workflow first; backend repair next. Both are part of the product, with explicit milestones.
- **Backend target:** Python 3.11+, FastAPI, Pydantic, SQLite, Gitleaks, watchdog, psutil, pytest/HTTPX, Ruff and restricted Docker jobs. Repair monitoring/sandbox dependencies are not installed by the Mac 1 implementation.
- **Dashboard:** Streamlit, initially using labelled fixtures. It displays backend decisions and never owns security decisions.
- **Tracks:** target Best Use of Gemma 4; maintain public open-source code for the open-source AI track. Confirm multiple-category and local-model eligibility with the organiser.
- **Licence:** MIT for this repository's original material. Model weights and dependencies retain their own licences.

Gemma is a practical selection for this hardware and event, not a proven best model for every use case. See the [model decision and trial](docs/MODEL_DECISION.md).

## Start here

1. Read the [final proposal](docs/FINAL_PLAN.md) and [team workflow](docs/TEAM_WORKFLOW.md).
2. Open your machine's task file below and paste its starter prompt into your coding assistant.
3. Read the [shared contract](docs/API_CONTRACT.md) before implementing an interface.
4. Keep unsupported capabilities labelled; follow the [coverage matrix](docs/COVERAGE.md).

| Member | Machine / coding assistant | Responsibility | Handoff |
|---|---|---|---|
| 1 — Abhijan | M4 Mac / Codex account 1 | API, privacy policy, Gemma, clipboard service, schemas, integration | [Mac 1](docs/tasks/MAC_1_BACKEND_GUARD.md) |
| 2 | Second Mac / Codex account 2 | Client adapters, incident/repair engine, sandbox, trusted verification, scheduler | [Mac 2](docs/tasks/MAC_2_BACKEND_REPAIR.md) |
| 3 | Windows / Antigravity | Dashboard, presentation components and API display client | [Windows 1](docs/tasks/WINDOWS_1_DASHBOARD.md) |
| 4 | Windows / Antigravity | Test-case specifications, fixture content, manual QA, demo and submission docs | [Windows 2](docs/tasks/WINDOWS_2_QA_DEMO.md) |

Both Mac owners own all backend, model, enforcement and repair logic. Windows work uses sample data until the backend interface is available. Development assistants help build DevGuard; their accounts are not DevGuard's runtime inference provider. Do not share account credentials.

## Documentation map

- [Architecture](docs/ARCHITECTURE.md)
- [Clipboard design](docs/CLIPBOARD.md)
- [Privacy and execution policy](docs/SECURITY_POLICY.md)
- [API and event contract](docs/API_CONTRACT.md)
- [Mac 2 integration signatures](docs/MAC_2_INTEGRATION.md)
- [Integrated setup and measured status](docs/INTEGRATION_STATUS.md)
- [Integration coverage](docs/COVERAGE.md)
- [Evaluation](docs/EVALUATION.md)
- [Demo runbook](docs/DEMO_RUNBOOK.md)
- [Setup and cloud budget](docs/SETUP_AND_BUDGET.md)
- [Implementation checklist](docs/IMPLEMENTATION_CHECKLIST.md)
- [Sources and third-party notices](THIRD_PARTY_NOTICES.md)
- [Contributing](CONTRIBUTING.md) and [coding-agent instructions](AGENTS.md)

## Important product boundary

Observing a clipboard or saved file is detection. Preventing a supported request requires a synchronous gate before delivery. Clipboard capture does not intercept every paste, and a standalone MCP server does not control an assistant's other tools. See coverage before making claims.

The [getting-started guide](docs/GETTING_STARTED.md) contains startup, clipboard controls and model smoke-test commands. Requests needing unavailable contextual analysis stay held. No real coding-client receiver is enrolled by default.
