# Member 3 — Windows / Antigravity: dashboard

**Current owner (16 October 2026): Mac 1 / Abhijan through the dashboard continuation chat, on `codex/windows1-continuation`, because the Windows 1 assistant quota is exhausted. Continue the integrated dashboard; do not rebuild it. See [active workflow](../TEAM_WORKFLOW.md). Original branch: `codex/windows-dashboard`. This is presentation and API consumption work, not backend policy/model logic.

## Ownership

`devguard/ui/`, `tests/ui/`, `docs/UI_NOTES.md`. Use Streamlit with a small display API client. Mac 1 owns dependency pins and shared schemas. Do not create a second FastAPI server, database schema, privacy classifier, clipboard OS watcher or repair engine.

## Read first

[README](../../README.md), [contract](../API_CONTRACT.md), [final plan](../FINAL_PLAN.md), [clipboard states](../CLIPBOARD.md), [coverage](../COVERAGE.md), [workflow](../TEAM_WORKFLOW.md).

## Build in order

1. Start against labelled synthetic responses from the API contract and Windows 2. Show a persistent **FIXTURE MODE — simulated presentation data** banner. Fixtures never count as actual model outcomes.
2. Build the privacy view: decision, redacted finding, safe preview, reason and delivered/not-delivered receipt.
3. Build clipboard view: enrolled host, enabled/status, content version, safe preview and last redacted finding. Do not display raw clipboard history. Do not label a pending or skipped scan safe.
4. Build coverage view: VERIFIED/PARTIAL/UNVERIFIED/UNSUPPORTED, client version and limitation text from backend data.
5. Add incident timeline and candidate diff/before-after verification views when backend responses are ready. No hidden reasoning or invented confidence/progress bars.
6. Switch the same display client to real endpoints. Store session tokens server-side and out of logs/Git. Handle 401, 409 stale, unavailable model and disconnection visibly.
7. Send operator actions to the backend and display its response; never simulate successful copy/send/apply in LIVE mode. Native clipboard actions target the capture host and need local confirmation; a Windows viewer cannot silently enable another Mac's capture.

Polish labels, readability and empty/error states. Do not add screenshots or screen recording as product features. Clipboard text protection remains central.

## Acceptance

Fixture and live modes are unmistakable; every action respects backend errors; no raw secrets or operator tokens appear; stale states are handled; unsupported Windows-native capture is clear; backend decisions are not recomputed in UI code. Add only focused UI tests where useful and document manual checks.

## Handoff

Provide actual UI start command after implementation, list views connected to live APIs, note fixture-only views and required contract changes. Keep mock data synthetic and presentation-only. Ask Mac 1 for endpoint/schema changes rather than editing backend code.

## Paste into Antigravity

> Work on DevGuard as Member 3 on branch codex/windows-dashboard. Read AGENTS.md, README.md, docs/API_CONTRACT.md, docs/CLIPBOARD.md, docs/COVERAGE.md and this task file. Build the Streamlit dashboard only in devguard/ui and related UI tests/notes. Use labelled fixture responses initially, then the same display API client for live backend responses. Build privacy, clipboard state, coverage, incident and patch-review views. The two Mac owners handle all backend, policy, model, native clipboard and repair logic; do not implement those here. Never fabricate live success or remove the fixture banner while simulated. Show redacted content only, keep tokens server-side, handle stale/unavailable/error states, and send actions to the backend for authoritative decisions. No screenshots/recording dependency. Preserve shared schemas and other teammates' work; report connected and fixture-only views separately.
