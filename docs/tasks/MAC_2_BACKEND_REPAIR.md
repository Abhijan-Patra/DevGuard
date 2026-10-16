# Member 2 — Mac / Codex: client adapters and backend repair

Branch: `codex/mac2-worker` when implementation starts. All tasks here are backend/execution logic; neither Windows member owns these decisions.

## Added QA/demo assignment — 16 October 2026

Mac 2 also takes over the Windows 2 scope. Read [the continuation handoff](MAC_2_WINDOWS_2_CONTINUATION.md) and [Windows 2 task](WINDOWS_2_QA_DEMO.md). Keep QA/demo changes on `codex/mac2-qa-continuation`, separate from active backend changes; record real measurements only.

## Ownership

`devguard/api/repair_routes.py`, `devguard/agent/`, `devguard/monitor/`, `devguard/repair/`, `integrations/`, `demo/backend/`, `trusted_tests/`, `tests/backend/`. Mac 1 owns API startup, shared schemas/auth and privacy/model infrastructure. Agree function signatures before crossing paths.

## Read first

[Final plan](../FINAL_PLAN.md), [architecture](../ARCHITECTURE.md), [contract](../API_CONTRACT.md), [policy](../SECURITY_POLICY.md), [coverage](../COVERAGE.md), [evaluation](../EVALUATION.md), [workflow](../TEAM_WORKFLOW.md).

## First milestone: supported coding-client path

Both Macs already use Codex. Inspect the installed version and documented hooks; test UserPromptSubmit blocking and selected PreToolUse actions with synthetic data. Determine actual coverage rather than assuming the desktop and CLI are identical. Do not add secret values to hook diagnostics.

Integrate with Mac 1's synchronous guard. If the prompt hook cannot rewrite, block and offer cleaned input for resubmission. Check tool file reads, shell-based reads, alternate tools, attachments and automatic context separately. A hook that only adds context is not sanitisation. A hook crash/timeout must not be misreported as enforced protection. Use the reference gate when a path is unsupported and label that gap.

Do not depend on buying Claude access. A Claude adapter is optional if available; test it independently. Do not attempt universal interception through screenshots, clipboard polling or HTTPS certificate replacement.

## Next milestone: first backend repair

1. Prepare one tiny FastAPI operation and independently specified failing pytest/HTTPX check; use Windows 2's scenario descriptions after Mac review of expected behaviour.
2. Create approved snapshots including relevant saved edits; record immutable base hashes and bounded diffs.
3. Run fixed baseline checks in a prepared, unprivileged Docker container with scope/network/resource limits; no host credentials or Docker socket in the target.
4. Use the same Gemma 4 E4B through Mac 1's validated adapter. Agent tools read allowed source, selected logs, configured service status and named test results. All tool outputs pass the guard.
5. Validate and apply genuine model proposals in the snapshot, rerun protected tests and scan the diff/report. No edits to the oracle, policy or expected values.
6. Return reviewable candidate or honest unresolved/blocked state. Implement cancellation and bounded attempts.
7. Recheck original hashes under lock before operator-approved apply; reject stale patches and implement idempotency.
8. Add saved-file queue/manual idle trigger; automatic idle heuristics come after the loop.

Source, diffs, structured logs, API probes and tests are the only diagnostic evidence needed. No screenshot, screen recording, video analysis or hardcoded successful patch.

## Handoff

Export a repair router and worker interface matching shared schemas. Supply real lifecycle events and safe evidence for the UI. List named tests, container image/dependencies, reset procedure and actual verification commands. Give Mac 1 the client capability evidence. Ask Mac 1 before schema/dependency edits.

## Acceptance

One actual adapter path is tested or clearly incomplete; one independent baseline failure becomes green after a genuine model source patch; originals and trusted tests stay unchanged; output is scanned; cancellation, unresolved and stale cases are recorded. Never claim production recovery from the local demo.

## Paste into Codex

> Work on DevGuard as Member 2 on branch codex/mac2-worker. Read AGENTS.md, README.md, docs/FINAL_PLAN.md, docs/API_CONTRACT.md, docs/SECURITY_POLICY.md, docs/COVERAGE.md and this task file. Own coding-client adapters, incident/repair routes, typed agent tools, snapshots, restricted runner, trusted verifier, patch lifecycle and scheduler. Test the installed Codex hook path with synthetic input first and integrate Mac 1's guard; unsupported paths must stay labelled. Use only the selected Gemma 4 E4B via the shared model interface. Diagnose bugs from source/diffs/structured logs/named API probes/tests, with no screenshot or recording dependency. Implement one genuine isolated repair and independent verification before expanding cases. Do not edit test expectations to pass. Keep final apply operator-controlled and stale-safe. Leave UI and Mac 1 shared schemas alone unless coordinated. Report actual tests, failures and coverage gaps without fabricated results.
