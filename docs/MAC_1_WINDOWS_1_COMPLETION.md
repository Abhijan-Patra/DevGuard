# Mac 1 and Windows 1 completion evidence — 16 October 2026

Integration branch: `codex/mac1-windows1-finish`. Combines dashboard PR #13 and Mac 1 PR #14 with main through PR #12. Mac 2 owns its repair trial and QA/demo work; none of those implementation files were changed here. The separate chat “Choose an open source model” is continuing the modern dashboard presentation after coordination authorized by Abhijan. This handoff supplies tested behavior and runtime evidence for that work.

## Completed changes

- A new privacy check clears the previous release card before it runs. Failed checks cannot leave an old approved decision active. Only READY ALLOW/SANITIZE cards offer delivery. Fixture delivery is isolated between dashboard sessions.
- Copy, disable, apply and reject messages require backend acknowledgement. Cleaned-copy displays the version returned by the native service. Existing backend policy, approval, base-hash and idempotency enforcement remains authoritative.
- LIVE mode requires the actual DevGuard status envelope. A missing or incompatible runtime stops the dashboard before text/action controls. The standalone mock demo server currently fails that contract and must not be presented as actual Gemma/repair execution; use the clearly labelled Fixture Mode for rehearsal. This schema check is not cryptographic authentication of arbitrary local software.
- The shared Ollama client pins the measured package digest in `devguard/config.py` and checks it after admission to the inference queue, before each inference POST. Missing/different packages hold without posting the input. Context is 4,096; privacy/tool output caps are 512/1,024; temperature 0; thinking off. No HTTP request can change the pin.
- Reproducible manual checks live in `devguard/clipboard/smoke.py` and `devguard/ui/smoke.py`. They use declared synthetic data and emit metadata/booleans, never clipboard originals, model prose or tokens.

## Measured verification

**198 automated tests passed**; one existing Starlette/HTTPX TestClient deprecation warning. `pip check`: no broken requirements. Tests use synthetic model/verifier ports; their count is not a real-model accuracy measurement.

Runtime: Apple M4 / 16 GiB (hardware from the existing Mac 1 handoff); macOS 26.6.2, Python 3.11.14, PyObjC Cocoa 12.2.2, Ollama 0.40.4. Current model metadata and both actual inference checks matched digest `dc35e8d9c6061baa6f0fa870975ab6932e2542b579b13ea0f199fa4bb7300c9c` for `gemma4:e4b-it-q4_K_M`.

| Actual check | Result and evidence |
|---|---|
| Private named Cocoa pasteboard + real Gemma/Gitleaks | All 12 checks PASS. No general clipboard access. Copy-to-finding 8.660 s. [Metadata](evidence/mac1-private-pasteboard.json) |
| System NSPasteboard + real Gemma/Gitleaks | Explicit user consent obtained in this chat. All 12 checks PASS. Copy-to-finding 2.427 s. Capture disabled and test content cleared afterward. [Metadata](evidence/mac1-system-clipboard.json) |
| Real loopback API + Streamlit element tree + real Gemma | SANITIZE in 2.179 s; actual local receiver got exactly the inspected cleaned bytes; replay held. All five views rendered, capture OFF, repair not configured, audit 0600 with no synthetic secret, backend shutdown acknowledged. [Metadata](evidence/mac1-live-dashboard.json) |

The native checks exercise OFF/no reads, enable skipping the already-present item, unchanged-counter/no reads, cleaned preview and native write, own-write suppression, stale-write refusal/newer-copy preservation, oversize/non-text SKIPPED, disable clearing transient records and no synthetic secret in audit. Four unchanged polls over about 3 s consumed 0.0011 s process CPU in each native trial. These are short individual samples, not peak resource or latency benchmarks. The system trial replaced the clipboard with known synthetic items before any content read; no preexisting private clipboard data was collected.

## Reproduce

From the selected checkout with the local model, Gitleaks and pinned Python/UI dependencies available:

```sh
python -m pytest -q -p no:cacheprovider
python -m pip check
python -m devguard.clipboard.smoke
python -m devguard.ui.smoke
```

The clipboard smoke defaults to an isolated named board. Its optional `--system-clipboard --consent` mode requires fresh operator approval because it replaces current clipboard contents; avoid other copying while it runs. Without `--consent`, that mode exits before constructing a native adapter. It always disables its test service afterward. The UI smoke starts a temporary backend on an available loopback port with an in-process reference receiver and a private temporary database; it leaves no running services and applies no patches.

## Remaining boundaries and ownership

Installed Codex interception/productive restricted tool access remains with Mac 2 and is unverified here. The real repair/stale/cancel/disposable-apply trial and QA/submission claims remain Mac 2's work. Its screenshot-reported `bb2ca43` / `codex/mac2-qa-demo` was not present on origin when checked, so it was not merged or overwritten.

The native bridge has no OS-wide atomic compare-and-swap: another application can race a write. These trials do not establish universal paste interception, Windows native capture, broad privacy accuracy or production recovery. The capture service starts OFF on normal app startup; the trial did not persist enablement. The ongoing presentation chat should preserve these boundary checks and evidence while improving the dashboard.
