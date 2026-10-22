## 0.3.0 — Windows support

- Add a PowerShell source installer/launcher and native Windows backend lifecycle with exact owned-process checks and graceful private-event shutdown.
- Add opt-in, bounded Unicode text clipboard capture with version checks, busy retries and cleaned-copy/held placeholders.
- Enforce Windows runtime ACLs, reparse/junction/device/alternate-stream refusal and pinned-parent source reads and writes; preserve POSIX boundaries.
- Add Windows native security tests and clean-wheel install CI for Python 3.11/3.12. Hardware/model and signed-in client workflow evidence remains platform-specific.

# Changelog

## 0.2.1 — 21 October 2026 · Verifier compatibility

- Prepare the local verifier as a single-platform image, with a tag derived from its public build inputs and preparation profile, instead of silently reusing the historical shared tag.
- Preserve failure metadata in release trials, including held repair state/reason, without logging exception payloads.
- Include the loopback-only legacy Streamlit configuration in the source archive.
- Retain the published 0.2.0 trial failures and distinguish dependency holds from model repair failures.

## 0.2.0 — 21 October 2026 · Public preview

- Publish a self-contained wheel and source distribution with the browser workspace, public demo source, independent oracle and minimal Docker build inputs.
- Add `devguard start`, `status`, `stop`, `doctor` and `serve`, plus a reviewable source installer and pinned runtime/optional-client dependencies.
- Separate installed runtime data from package files; retain checkout-local data for source users. Add private-file checks, launcher locking and occupied-port refusal.
- Add privacy-only startup without Docker. Preserve required opt-in macOS clipboard capture and placeholder previews; held copies remain noncopyable.
- Document supported hardware/platform scope, first-run steps, project enrollment, troubleshooting, updates, security reporting and support.
- Verify clean wheel installations separately from editable development installs. Record a real local Gemma/Docker repair, disposable reviewed apply and rollback through the installed package.

This is a preview with finite model/test coverage. Native Windows/Linux clipboard capture, broad unseen classification accuracy, universal client interception and production recovery are not established.
