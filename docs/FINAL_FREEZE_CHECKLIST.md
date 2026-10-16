# DevGuard final review checklist — 16 October 2026

Mac 2 continues the assigned QA/demo handoff. Checked entries describe measured work; unchecked entries remain team actions.

- [x] Integrated automated suite: **223 passed**; one existing Starlette/HTTPX deprecation warning. `pip check` clean.
- [x] Mac 2 source Ruff/whitespace checks and new-commit Gitleaks scan passed; no private runtime files staged. This is a scoped scan, not certification of every repository commit.
- [x] Exact Gemma package/digest recorded; context 4096, privacy/tool output 512/1024, temperature 0, thinking off. Inference refuses a different/missing digest.
- [x] Real local Gemma/guard/API/Docker: baseline FAIL → genuine patch → independent PASS → approved disposable APPLIED → idempotent repeat → post-apply PASS; source/tests unchanged and worker stopped.
- [x] Real stale apply returned 409 STALE_SOURCE, preserved the concurrent edit and marked the run OBSOLETE; queued cancellation created no candidate.
- [x] Real local reference receiver got exactly the inspected bytes; replay held; all five live views rendered. Installed Codex interception is still unverified.
- [x] Mac 2 isolated native pasteboard passed 12 checks without general clipboard access. Distinct general clipboard input was HELD; cleaned-copy did not run; capture confirmed OFF. Both results documented.
- [x] Catalogue/registry audit found five missing withheld records; added metadata-only UNRUN entries. All **26** records remain UNRUN, unique IDs/statuses match and each record validates against its schema. No expected outcomes or withheld input were altered.
- [x] Runbook/submission wording distinguishes actual experiments, fixture presentation and unverified paths. No placeholder video URL or 100% accuracy claim remains in current submission text.
- [x] Abhijan merged worker PR #16, including the coordinated verifier exception-reporting change. All business assertions remain unchanged.
- [x] Abhijan merged QA continuation PR #17 and modern dashboard PR #18. Mac 2 integrated the published dashboard and verified all six live views without errors/exceptions.
- [ ] Team opens the actual Live Mode dashboard and rehearses its current ready candidate. Keep the Mac awake, power connected, Docker/Ollama running, capture OFF unless fresh consent is given.
- [ ] Team confirms the hackathon form's category fields, reviews the prepared text, adds a real recording only if required and submits before **4:30 PM IST**. Creating GitHub documents is not submitting the form.

Measured references: [repair](../devguard/repair/README.md), [evaluation](EVALUATION.md), [runbook](DEMO_RUNBOOK.md), [submission text](SUBMISSION_FINAL.md). The queued foreground priority does not preempt active inference; default model/clipboard/privacy limits can still hold requests.
