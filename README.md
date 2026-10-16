# DevGuard

**A local Gemma-powered privacy guard and backend repair agent for AI-assisted development.**

Status: proposed implementation and team handoff. This repository currently contains planning documents, not a working application. No repair, privacy or performance results have been established yet.

DevGuard inspects supported prompts, file access, tool results and copied text; it also investigates reproducible backend failures and prepares independently tested patches in a disposable workspace. Clipboard capture is a required, opt-in feature. Bug diagnosis uses source, structured logs, diffs, named API probes and tests; it does not depend on screenshots or screen recordings.

## Decisions

- **One model:** Gemma 4 E4B through Ollama, initially `gemma4:e4b`. Different task prompts share one model and inference queue.
- **Priority:** privacy and clipboard workflow first; backend repair next. Both are part of the product, with explicit milestones.
- **Backend:** Python 3.12, FastAPI, Pydantic, SQLite, Gitleaks, watchdog, psutil, pytest/HTTPX, Ruff and restricted Docker jobs.
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
- [Integration coverage](docs/COVERAGE.md)
- [Evaluation](docs/EVALUATION.md)
- [Demo runbook](docs/DEMO_RUNBOOK.md)
- [Setup and cloud budget](docs/SETUP_AND_BUDGET.md)
- [Implementation checklist](docs/IMPLEMENTATION_CHECKLIST.md)
- [Sources and third-party notices](THIRD_PARTY_NOTICES.md)
- [Contributing](CONTRIBUTING.md) and [coding-agent instructions](AGENTS.md)

## Important product boundary

Observing a clipboard or saved file is detection. Preventing a supported request requires a synchronous gate before delivery. Clipboard capture does not intercept every paste, and a standalone MCP server does not control an assistant's other tools. See coverage before making claims.

The first engineering step is the measured model/tool trial and an actual guarded request. Installation instructions are in the setup document; application start commands will be added when executable code exists.
