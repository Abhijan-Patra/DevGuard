# DevGuard QA status — 16 October 2026

Catalogue reporting is separate from real-model experiments. This command does not run the scenarios or mark any pass. Mac 2 continues Windows 2's assigned QA/demo scope.

| Catalogue file | Cases |
|---|---:|
| clipboard_cases | 6 |
| privacy_cases | 7 |
| repair_cases | 8 |
| withheld_variants | 5 |

**Registry:** 26 unique records; UNRUN 26, PASS 0, FAIL 0, BLOCKED 0. Catalogue IDs/statuses match the registry. Withheld inputs remain outside runtime prompts/tuning. Fixture/schema tests do not execute these cases.

## Separate measured evidence

- Integrated automated suite: **209 passed**, one existing dependency deprecation warning; pip check clean. These include mocked model/verifier ports and are not an accuracy benchmark.
- Real Gemma/guard/API/Docker cart trial: baseline FAIL -> genuine patch -> independent PASS -> disposable approved apply -> idempotent repeat -> post-apply PASS; 46.07 s; original/tests unchanged and worker stopped. See [repair evidence](../devguard/repair/README.md).
- Real stale/cancel trial: 409 STALE_SOURCE, concurrent edit preserved, state OBSOLETE; queued cancel produced no candidate; 42.19 s.
- Mac 2 isolated named pasteboard: all 12 checks passed, 1.550 s copy-to-finding, no general clipboard access. See [metadata](results/mac2-private-pasteboard.json).
- Mac 2 consented general clipboard combined input: HELD/REVIEW, cleaned-copy not executed; capture OFF. The failed input remains in [metadata](../devguard/repair/verification/mac2-system-clipboard-held.json).
- Mac 2 real local reference receiver + five live views: PASS, replay held, 1.282 s synthetic privacy evaluation; see [metadata](results/mac2-live-dashboard.json). Mac 1 separately records its own [measurements](../docs/MAC_1_WINDOWS_1_COMPLETION.md).

These experiments are not retrospectively assigned catalogue passes: some older catalogue test names/field names are conceptual and do not match the cart manifest. Preserve expected behavior and reconcile each mapping before future execution. No privacy precision/recall, full unseen evaluation, production recovery or installed-client interception result is claimed.

See [runbook](../docs/DEMO_RUNBOOK.md), [evaluation](../docs/EVALUATION.md) and [submission text](../docs/SUBMISSION_FINAL.md). Mock server data is rehearsal only; the live UI requires the actual backend contract.
