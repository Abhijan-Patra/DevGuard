# Modern operator dashboard — 16 October 2026

Branch: `codex/mac1-dashboard`. Built on the merged team dashboard and the Mac 1 completion handoff, preserving PR #13/#14/#15 behavior. Mac 2 retains the repair engine, client adapters and final repair/demo evidence. The dashboard consumes their actual APIs; it does not implement a second classifier or repair worker.

## Available in the dashboard

| View | Operator workflow |
|---|---|
| Overview | Actual model readiness, clipboard state, worker state, waiting inference count, digest, audit durability, feature navigation and a bounded audit-page preview |
| Privacy gate | Synthetic examples or custom text, task/surface/version/destination, local inspection, decision/reasons/cleaned preview, enrolled delivery receipt, transient active findings |
| Text clipboard | Supported capture host, explicit consent, optional task context, enable/disable, inspection state and version, safe preview and acknowledged copy-cleaned action |
| Repair & patches | Trusted initialization retry, named incident creation/investigation, manual idle, pause, run cancellation, actual baseline/verification/reason/tool activity, guarded patch diff, apply/reject with inspected candidate/base and idempotency fields |
| Audit event log | Event-kind/severity filters, bounded cursor pagination and export of displayed redacted metadata |
| Integration coverage | Runtime capability limits and expandable recorded synthetic native/API/Gemma verification reports; recorded trials are distinct from continuous/live readiness |

Newly queued fixture investigations remain simulated QUEUED runs. They never become fabricated successful patches. Live mode refuses an invalid status envelope before inspection/action controls and never falls back to fixture decisions. A local-preview inspection offers no outgoing delivery button because no receiver is enrolled for it.

## Open locally

Start the backend from this checkout; optionally supply its trusted, already-prepared verifier image as documented in INTEGRATION_STATUS.md:

```sh
.venv/bin/python -m devguard
.venv/bin/python -m streamlit run devguard/ui/app.py --server.address 127.0.0.1
```

Open **http://127.0.0.1:8501**. The default is clearly labelled Fixture Mode. Choose **Live Mode**, then **Connect on this Mac** in connection settings. This explicit action reads only the private local operator token for the default port 8765; it keeps that token in non-widget server session state and never fills the password field. Manual operator enrolment remains available. Changing the endpoint revokes the automatically loaded credential and clears prior results/audit-page state. Disconnect clears credentials and result state.

Connection never enables capture or resumes repair. Native capture requires its separate local consent action. Streamlit and the backend stay loopback-only; this release does not expose the operator dashboard publicly or create paid cloud infrastructure. Source is published through the repository review branch.

The local CSS provides a dark navigation rail, light workspace, readable status cards, unified typography, consistent spacing, restrained color and narrow-layout rules. All design assets are local; no remote font/image request is needed. Actual desktop views were visually checked in the browser. Screenshots are presentation QA only and are not inputs/dependencies of privacy or backend bug diagnosis.

## Verification

- **212 automated tests passed** on the combined build. `pip check` reported no broken requirements. One upstream Starlette/HTTPX deprecation warning remains.
- New meaningful tests cover overview navigation, fixture queue behavior, actual authenticated control routes without model work, operator credential handling, malformed connection URLs, destination changes and acknowledgement holds.
- Real `python -m devguard.ui.smoke`: **PASS** with the exact pinned local Gemma. A synthetic input produced SANITIZE in **7.745 s**; the local reference receiver got exactly the inspected cleaned bytes; replay was held; all six live views rendered; audit excluded the synthetic secret and remained 0600; temporary backend shutdown was acknowledged. This is a single measured trial, not a latency or accuracy guarantee. [Metadata](evidence/mac1-modern-dashboard.json)
- User-consented native macOS clipboard verification is complete, with capture disabled and synthetic text cleared afterward. The coordinated full native run passed 12 checks. [Native evidence](evidence/mac1-system-clipboard.json)
- The running local dashboard was checked against the actual operator API. Current startup defaults remain capture OFF and repair PAUSED.

Installed Codex/Claude interception, universal paste blocking and Mac 2's final exact repair/stale/cancel/disposable-apply proof are separate coverage rows. Do not turn an inspection preview, fixture walkthrough, passing UI test or earlier local experiment into those claims.
