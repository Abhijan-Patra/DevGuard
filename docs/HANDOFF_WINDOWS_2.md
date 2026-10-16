# Windows 2 QA/demo continuation handoff

Mac 2 continues the reassigned QA/demo work on `codex/mac2-qa-continuation`, alongside worker PR [#16](https://github.com/Abhijan-Patra/DevGuard/pull/16). Mac 1 retains the dashboard implementation.

The existing catalogue has 26 synthetic scenarios: privacy 7, clipboard 6, repair 8, withheld 5. The original registry had 21 entries; the five missing withheld metadata records were added without exposing inputs or changing expectations. All 26 remain UNRUN. The reporter now rejects missing/duplicate IDs or mismatched statuses. Schema/fixture tests are not live case execution.

Separate measured experiments now cover a real Gemma/API/guard/Docker passing repair, disposable approved/idempotent apply, stale rejection, queued cancel, local reference delivery/replay, five live UI views and a private native pasteboard. The distinct consented general clipboard input was HELD and stays recorded. Source/test hashes and worker shutdown were checked; capture is OFF. See [evaluation](EVALUATION.md) and [repair metadata](../devguard/repair/README.md).

Current combined test result: **210 passed**; pip check clean; scoped Ruff, whitespace and new-commit secret scan clean. One dependency deprecation warning remains. No catalogue accuracy percentage, peak resource benchmark, universal interception or production-recovery claim is made.

Use [the current runbook](DEMO_RUNBOOK.md) and [prepared submission text](SUBMISSION_FINAL.md), with [the final checklist](FINAL_FREEZE_CHECKLIST.md). The newer mock server matches the live response envelope, but its outputs remain simulated rehearsal data rather than actual model execution. Installed Codex interception remains unverified. Automatic OS-idle scheduling and arbitrary-project enrollment remain unfinished.

Abhijan should review/merge the worker and QA PRs, reconcile the modern presentation branch, then the team should rehearse and submit before 4:30 PM IST. No hackathon form or recording is submitted by this handoff.
