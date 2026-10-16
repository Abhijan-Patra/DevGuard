# Mac 2: continue Windows 2 QA and demo work

Assigned by Abhijan on 16 October 2026 after both Windows assistants exhausted their quotas. This is an added responsibility alongside [Mac 2 backend work](MAC_2_BACKEND_REPAIR.md). Mac 1's dashboard continuation chat takes Windows 1.

## Scope and starting point

Use your own checkout and a `codex/mac2-qa-continuation` branch based on the latest integrated code. Read `AGENTS.md`, [the API contract](../API_CONTRACT.md), [the integration status](../INTEGRATION_STATUS.md), [the original Windows 2 task](WINDOWS_2_QA_DEMO.md) and [the existing handoff](../HANDOFF_WINDOWS_2.md). The existing scenario catalogue and fixture data are already present; audit and extend them rather than replacing them.

You now own `evals/cases/`, `evals/results/`, `demo/fixtures/`, `docs/DEMO_RUNBOOK.md`, `docs/EVALUATION.md` and `docs/SUBMISSION_DRAFT.md`. Keep dashboard implementation and `tests/ui/` with Mac 1. Any evaluation runner or trusted-test change stays part of your backend scope and needs the existing Mac reviews. Do not alter expected outcomes to make a run pass.

## Work in order

1. Validate the existing case IDs, counts, result registry and contract-v1 fixture events. Keep the withheld variants out of model prompts and tuning examples. Use synthetic input only.
2. Reconcile older handoff claims with the current checkout. A fixture/schema test passing is not a case execution. Leave each unexecuted case `UNRUN`; record `BLOCKED` only with a real attempted check and its safe reason.
3. Rehearse fixture mode with its banner. Then check live dashboard empty/error states, unavailable model, held delivery, stale clipboard copy and stale patch apply. Use redacted receipts, event IDs and named test output as evidence. Do not enable native capture or apply source patches merely to complete a checklist; those actions require the operator's explicit consent/review.
4. Obtain current measured evidence from Mac 1 for model digest/settings, privacy outcomes, delivery scope and runtime versions. Record setup and scope alongside every result. Do not copy old status prose into fresh measurements.
5. For repair, preserve independently specified expected behaviour. Record baseline failure, model-generated candidate, unchanged verifier result, source-hash checks and whether application was requested. An unresolved/blocked repair stays unresolved/blocked.
6. Update runbook and submission wording to match actual evidence. Required opt-in macOS text capture stays in scope; Windows native capture and unrelated-app paste interception remain unsupported. Separate the local reference gate from installed-client interception.

## Dashboard checks to include

- A successful privacy evaluation followed by a failed replacement check leaves no old release card.
- CHECKING, FAILED, EXPIRED, missing-status and LOCAL_ONLY decisions offer no external release action.
- Switching fixture/live mode, URL or token clears previous privacy results.
- Cleaned-copy success uses the returned clipboard version; held or unacknowledged actions show no success.
- Apply/reject reports success only when the backend acknowledges the corresponding patch state. Stale responses preserve the source and show a conflict.
- Fixture delivery cannot mark a newly started dashboard session as delivered.

## Handoff

Return the branch/commit, actual commands and results, case counts by result, remaining UNRUN/BLOCKED items and safe evidence references. Flag schema/dependency requests to Mac 1. Do not publish the submission or claim a remote session has run merely because this file exists.

## Paste into Mac 2 Codex

> Abhijan has reassigned Windows 2's QA/demo scope to you because the Windows assistants exhausted their quotas. Continue your existing Mac 2 backend role and take the additional scope in docs/tasks/MAC_2_WINDOWS_2_CONTINUATION.md, using a separate codex/mac2-qa-continuation branch. Read AGENTS.md, docs/API_CONTRACT.md, docs/TEAM_WORKFLOW.md and both relevant task files. Audit the existing synthetic cases, fixtures and result registry; run available meaningful checks; record actual results; update demo, evaluation and submission wording to measured capabilities. Keep unrun checks UNRUN and fixture data labelled. Coordinate real model evidence and shared changes with Mac 1. Leave devguard/ui and tests/ui to the dashboard continuation chat. Preserve private data, operator consent, independent expected outcomes and existing edits. Report the branch, commands, results and remaining gates.
