# Four-member workflow and ownership

One repository; four separate clones and branches. Never share Codex/Antigravity credentials. Do not work inside another person's live checkout.

## Assignments

| Member | Branch to create when coding starts | Owned implementation paths |
|---|---|---|
| Mac 1 — Abhijan / Codex | `codex/mac1-guard` | `devguard/api/app.py`, `devguard/api/guard_routes.py`, `devguard/schemas/`, `devguard/guard/`, `devguard/models/`, `devguard/clipboard/`, `devguard/storage/` |
| Mac 2 — Codex | `codex/mac2-worker` | `devguard/api/repair_routes.py`, `devguard/agent/`, `devguard/monitor/`, `devguard/repair/`, `integrations/`, `demo/backend/`, `trusted_tests/`, `tests/backend/` |
| Windows 1 — Antigravity | `codex/windows-dashboard` | `devguard/ui/`, `tests/ui/`, `docs/UI_NOTES.md` |
| Windows 2 — Antigravity | `codex/windows-qa` | `evals/cases/`, `evals/results/`, `demo/fixtures/`, `docs/DEMO_RUNBOOK.md`, `docs/EVALUATION.md`, `docs/SUBMISSION_DRAFT.md` |

Mac 1 owns shared schemas, dependency configuration, auth, policy and final integration. Mac 2 proposes changes to shared schemas before using them. Windows owners request API changes rather than recreating backend decisions in the dashboard. Mac 2 implements test runners and acceptance-test code; Windows 2 supplies test descriptions, expected examples and manual observations. Mac 1 reviews independent expected outcomes.

No assignment above means code already exists. Paths are agreed targets.

## First shared checkpoint

Read [API_CONTRACT.md](API_CONTRACT.md). Mac 1 creates the schema definitions and fixture response; Mac 2 confirms typed-tool and patch requirements. Windows 1 builds fixture-mode screens without waiting for a model server. Windows 2 prepares unseen synthetic case content without teaching the model their answers.

The two Mac owners integrate early: first real privacy decision, clipboard event and adapter interception before expanding repair cases. Keep a short STATUS note in each pull request: implemented, tested, unresolved, handoff needed.

## Merge discipline

- Create small pull requests targeting `main`; do not overwrite another member's work.
- Shared API/policy changes need Mac 1 review; trusted verifier and apply changes need both Mac owners' review.
- Frontend fixture mode must remain visibly labelled after live integration.
- Windows contributors may improve docs in their scope; security/model/contract edits are proposed to the Mac owners first.
- Record actual test commands and results; unrun checks are unrun, not passing.
- No raw secrets, clipboard history, model weights, personal logs, account tokens or disposable snapshots in commits.

## Suggested checkpoints

1. Contract and task ownership agreed.
2. Mac 1 model trial + guard; Mac 2 actual client adapter trial; Windows screens and case catalogue.
3. Real clipboard flow + outgoing evidence; first independent backend failure prepared.
4. Optional repair loop + dashboard live data; failure and stale cases.
5. Freeze, evaluate and submit the actual supported capabilities.

Use remaining time rather than assuming the original eight-hour proposal still applies. Reserve the last hour for integration and presentation. Optional cloud work never blocks the local proof.

## Each member's first action

Clone `https://github.com/Abhijan-Patra/DevGuard.git`, read `AGENTS.md`, this document, the API contract and your task file. Branch from the latest `main`. The task file includes a paste-ready assistant prompt. Build only your owned slice and surface dependencies early.
