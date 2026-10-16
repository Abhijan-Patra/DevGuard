# Member 4 — Windows / Antigravity: scenarios, QA and demo

Branch: `codex/windows-qa` when implementation starts. This role supplies useful parallel specifications and presentation materials without owning backend/execution logic.

## Ownership

`evals/cases/`, `evals/results/`, `demo/fixtures/`, `docs/DEMO_RUNBOOK.md`, `docs/EVALUATION.md`, `docs/SUBMISSION_DRAFT.md`. The Mac owners implement test runners, trusted tests and the demo backend. Do not change backend source or expected outcomes to obtain a passing result.

## Read first

[Final plan](../FINAL_PLAN.md), [contract](../API_CONTRACT.md), [evaluation](../EVALUATION.md), [clipboard](../CLIPBOARD.md), [runbook](../DEMO_RUNBOOK.md), [workflow](../TEAM_WORKFLOW.md).

## Build in order

1. Create concise scenario records: ID, synthetic input, task, expected policy/behaviour, what should remain useful and whether execution is UNRUN. Use `.invalid` example domains and declared fake credential fixtures; never real data.
2. Include benign text, contextual confidential prose, unnecessary customer details, prompt-injection text, rapid clipboard changes, copy-cleaned, oversized/non-text capture and unavailable-model cases.
3. Provide UI sample events matching contract v1 to Windows 1, labelled synthetic fixtures. They are not runtime decision rules or model results.
4. Specify backend expected behaviours in simple tables for Mac 2: null handling, normal request, cart quantity calculation, healthy backend, unresolved failure and stale candidate. Mac owners approve the oracle and implement the independent verifier.
5. Keep several input variants withheld from model examples and prompt tuning. Sharing fixture IDs is fine; do not implement a lookup that chooses a prewritten redaction/patch.
6. Run manual dashboard checks when live services are available; record actual outcomes and safe evidence. Leave not-run cases UNRUN.
7. Update demo and submission wording to exactly the implemented capabilities, actual hardware/model and supported client/clipboard hosts. Do not claim unsupported Antigravity protection.

No Docker/model/native-capture setup is required for drafting cases. No screenshots or recordings are diagnostic inputs; demonstration evidence can be redacted request receipts, event IDs and test results.

## Acceptance

The case catalogue covers failures as well as successes, UI fixtures match the contract, no actual private values are included, tests and model outputs are not invented, and submission text separates implemented privacy/clipboard from any incomplete repair work.

## Handoff

Give Windows 1 fixture events, Mac 1 privacy/clipboard cases and Mac 2 backend behaviour tables. Provide a short result summary with counts, unrun items and gaps. Ask Mac owners to confirm measurements and actual supported coverage before publishing claims.

## Paste into Antigravity

> Work on DevGuard as Member 4 on branch codex/windows-qa. Read AGENTS.md, README.md, docs/API_CONTRACT.md, docs/EVALUATION.md, docs/CLIPBOARD.md and this task file. Own synthetic scenario specifications, labelled dashboard fixtures, manual QA records, demo runbook and submission draft in the assigned paths. Do not build backend, repair, model, native clipboard or security logic; the two Mac owners handle those. Prepare positive, benign, contextual-confidentiality, rapid-copy/stale, unavailable-model, unresolved-repair and forbidden-access cases. Keep some variants out of model prompts, use no real secrets, and never present fixture data as executed results. Give Windows 1 contract-compatible sample events and give the Mac owners independent expected-behaviour tables. Record actual manual results when available and leave unrun cases UNRUN. No screenshot/recording dependency for bug diagnosis; preserve clipboard capture in the product description.
