# DevGuard

**A local Gemma-powered privacy guard and backend repair agent for AI-assisted development.**

The primary interface is now a purpose-built local browser workspace with dark/light themes, context inspection, managed source reads, opt-in native text capture, repair review/apply/rollback, project monitoring and redacted audit. All runtime work runs on one laptop. See [single-laptop setup](docs/PROFESSIONAL_WORKSPACE.md) and [current completion evidence](docs/PROFESSIONAL_STATUS.md).

```sh
./scripts/devguard-local start
```

Open **http://127.0.0.1:8765/app** and choose **Connect this browser**. Clipboard capture and source watchers start OFF; the worker starts paused. The default repair project is a disposable copy, so demonstration apply/rollback does not change the repository fixture.

The [modern operator dashboard](docs/DASHBOARD_RELEASE.md) exposes all six implemented views and the actual backend controls. It runs locally at **http://127.0.0.1:8501**; choose Live Mode and Connect on this Mac. The combined release passes **212 tests**, with a real pinned-Gemma/reference-delivery smoke and completed native clipboard checks. Unsupported client paths remain labelled.

DevGuard inspects supported prompts, file access, tool results and copied text; it also investigates reproducible backend failures and prepares independently tested patches in a disposable workspace. Clipboard capture is a required, opt-in feature. Bug diagnosis uses source, structured logs, diffs, named API probes and tests; it does not depend on screenshots or screen recordings.

## Decisions

- **One model:** Gemma 4 E4B through Ollama, using the explicit local Q4 tag `gemma4:e4b-it-q4_K_M`. Different task prompts share one model and inference queue.
- **Priority:** privacy and clipboard workflow first; backend repair next. Both are part of the product, with explicit milestones.
- **Backend target:** Python 3.11+, FastAPI, Pydantic, SQLite, Gitleaks, watchdog, psutil, pytest/HTTPX, Ruff and restricted Docker jobs. Repair monitoring/sandbox dependencies are not installed by the Mac 1 implementation.
- **Dashboard:** A dedicated HTML/CSS/JavaScript workspace served by the existing FastAPI backend. The legacy Streamlit UI and isolated public demo remain available. The UI displays authoritative backend decisions and does not own security policy.
- **Tracks:** target Best Use of Gemma 4; maintain public open-source code for the open-source AI track. Confirm multiple-category and local-model eligibility with the organiser.
- **Licence:** MIT for this repository's original material. Model weights and dependencies retain their own licences.

Gemma is a practical selection for this hardware and event, not a proven best model for every use case. See the [model decision and trial](docs/MODEL_DECISION.md).

## Original team planning (historical)

All former machine roles are now handled on this laptop, per the user's 21 October instruction. The task files below remain as implementation history. Start with the single-laptop guide above.

### Original starting sequence

1. Read the [final proposal](docs/FINAL_PLAN.md) and [team workflow](docs/TEAM_WORKFLOW.md).
2. Open your machine's task file below and paste its starter prompt into your coding assistant.
3. Read the [shared contract](docs/API_CONTRACT.md) before implementing an interface.
4. Keep unsupported capabilities labelled; follow the [coverage matrix](docs/COVERAGE.md).

| Member | Machine / coding assistant | Responsibility | Handoff |
|---|---|---|---|
| 1 — Abhijan | M4 Mac / Codex account 1 | API, privacy policy, Gemma, clipboard service, schemas, integration | [Mac 1](docs/tasks/MAC_1_BACKEND_GUARD.md) |
| 2 | Second Mac / Codex account 2 | Client adapters, incident/repair engine, sandbox, trusted verification, scheduler | [Mac 2](docs/tasks/MAC_2_BACKEND_REPAIR.md) |
| 3 | Mac 1 / Codex dashboard continuation (Windows 1 quota exhausted) | Dashboard, presentation components and API display client | [Windows 1](docs/tasks/WINDOWS_1_DASHBOARD.md) |
| 4 | Mac 2 / Codex (Windows 2 quota exhausted) | Test-case specifications, fixture content, manual QA, demo and submission docs | [Windows 2](docs/tasks/WINDOWS_2_QA_DEMO.md) |

The [active reassignment](docs/TEAM_WORKFLOW.md#active-reassignment--16-october-2026) records the Windows quota handoff. Mac 1 continues the dashboard in an isolated branch; Mac 2 receives the [QA/demo continuation task](docs/tasks/MAC_2_WINDOWS_2_CONTINUATION.md).

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

## Guarded coding-client source tools

The native Codex/Claude CLI integration now has isolated prompt/MCP boundary trials with the real Gemma guard and a synthetic local provider receiver. The two managed tools list/read registered source; they cannot run shell commands or apply changes. [Client setup and limits](docs/CLIENT_INTEGRATION.md), [measured native evidence](docs/evidence/professional-native-clients.json), [privacy calibration](docs/evidence/professional-privacy-calibrated.json) and [additional regression cases](docs/evidence/professional-privacy-variants.json). Earlier failures remain preserved; no universal or perfect-detection claim.
