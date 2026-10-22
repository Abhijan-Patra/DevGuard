# Install DevGuard

DevGuard 0.3.1 is a local **public preview**, not a hosted protection service. The public website is a read-only tour. To inspect your own text, clipboard or project, run the application on your machine.

Windows users: follow the [PowerShell guide](WINDOWS.md). The shell commands below target macOS/Linux.

## Before installation

| Requirement | Purpose |
|---|---|
| Python 3.11 or 3.12 | Tested installation/runtime versions; no Node.js is needed to run the app. |
| Ollama | Runs the fixed local Gemma model. Open the app after installing it. Local inference needs no cloud API key. |
| Gitleaks | Required credential scanner. macOS with Homebrew: `brew install gitleaks`. |
| Docker Desktop/Engine | Required for backend repair only. Open it and complete its setup/terms yourself. |
| macOS/Windows desktop | Native text clipboard capture. See [Windows installation](WINDOWS.md). Linux native capture remains unsupported. |

Use an Apple silicon Mac with 16 GB memory for the measured configuration. Other hardware may be slower or run out of memory; no minimum-performance guarantee is made. Leave ample disk space for Python packages, Docker and the roughly 6.6 GB selected Ollama package. Model/image downloads need network access; running the prepared sandbox has no network access.

Official installers: [Python](https://www.python.org/downloads/), [Ollama](https://ollama.com/download), [Gitleaks](https://github.com/gitleaks/gitleaks#installing), [Docker for Mac](https://docs.docker.com/desktop/setup/install/mac-install/). The [selected package](https://ollama.com/library/gemma4:e4b-it-q4_K_M) is checked against its pinned digest. Ollama's [local setup](https://docs.ollama.com/quickstart) differs from its optional cloud products. External tools have their own licences and terms.

## Install from GitHub

Use a fresh directory. Review the installer in `scripts/setup.sh`; it uses no `sudo`, remote shell installer or global client-config changes.

```sh
git clone https://github.com/Abhijan-Patra/DevGuard.git
cd DevGuard
./scripts/setup.sh
./scripts/devguard-local start
```

If your Python command is named differently, set `DEVGUARD_PYTHON=/absolute/path/to/python3.11` for the setup command. Keep the checkout in place after editable installation. Its runtime data is stored privately under `.devguard/`, excluded from Git. Do not commit or share that directory.

The launcher checks prerequisites, can open installed Ollama/Docker applications on macOS, downloads **only** `gemma4:e4b-it-q4_K_M` if absent, and builds a restricted verifier from two packaged public files. An active exact-tag download is left alone. Large downloads may take time; terminal progress is not a stalled process. Missing external applications, occupied ports and mismatched model digests stop startup with an actionable message.

## Install a release wheel

Download `devguard-0.3.1-py3-none-any.whl` and `SHA256SUMS` from the [GitHub release](https://github.com/Abhijan-Patra/DevGuard/releases/latest). Compare its checksum with `shasum -a 256 devguard-0.3.1-py3-none-any.whl`. Then, in the download directory:

```sh
python3.11 -m venv .devguard-venv
. .devguard-venv/bin/activate
python -m pip install './devguard-0.3.1-py3-none-any.whl[clipboard,client]'
devguard start
```

This is a GitHub distribution; `pip install devguard` from an unrelated package index is not the documented installation route. We have not published this release to PyPI.

The wheel includes the workspace assets, public demo, independent cart tests and Docker build inputs. It does not require the source checkout. The default private workspace is `~/.devguard-workspace/`; installed package files are never used as mutable runtime storage. Source installs retain their checkout-local workspace for compatibility. `DEVGUARD_HOME` selects another canonical, non-symlink directory; use the same value for start, status, stop and client setup. Do not share one workspace between users.

Native client profiles are optional. The client extra installs their SDK; it does not sign you in or grant hook trust. See [client setup](CLIENT_INTEGRATION.md) for the tested versions and restricted paths.

## First run

1. Open `http://127.0.0.1:8765/app` and click **Connect this browser**. This pairs the browser with your local operator controls for eight hours; no account is needed for the dashboard.
2. Try **Context gate** with a declared synthetic value, for example `Debug login: password=synthetic-example-123456; ValueError at auth.py:42`. Approved text should show a credential placeholder. **Release to composer** is a separate explicit action; it does not send to a cloud assistant.
3. For **Text clipboard**, check the local consent box and enable capture. Copy new text after enabling. The existing clipboard is skipped. Sensitive values show placeholders; held results show a whole-copy marker. **Copy cleaned text** performs a version-checked write; observation does not silently replace your clipboard.
4. For **Backend repairs**, select the disposable `demo-cart` project and `cart` check, queue investigation, and resume the worker. Review its actual result and diff. A held/unresolved run is possible; no success is simulated. Apply requires review and exact hashes. Rollback is session-only and refuses concurrent source edits.
5. Disable capture when finished. Stop DevGuard with the same launcher. Starting it again clears transient candidates/composer and begins with capture/watchers off and repairs paused.

Do not test using real credentials. The guard is an aid with finite detection coverage.

## Run only privacy features

```sh
./scripts/devguard-local start --privacy-only
# Installed wheel:
devguard start --privacy-only
```

This mode still requires Ollama, the exact model and Gitleaks. It does not start Docker or register a repair project. For foreground troubleshooting/API development use `devguard serve --port 8765`; this starts the control service even when dependencies are unavailable, and affected inspections remain held. Stop a foreground process with Ctrl+C. Do not run it alongside the managed instance on the same port.

## Troubleshooting

Run `./scripts/devguard-local doctor` (or `devguard doctor` for a wheel). `--json` produces metadata-only diagnostics. `--privacy-only` omits Docker from required checks. Doctor never reads clipboard contents, runs model inference or installs anything.

| Symptom | Next step |
|---|---|
| Python not found/version rejected | Install Python 3.11/3.12; rerun setup with the intended interpreter. |
| Ollama unavailable | Open Ollama. On Linux start its local service or `ollama serve`; no remote endpoint is supported. |
| Model not installed | `ollama pull gemma4:e4b-it-q4_K_M`, then retry. Let an active download finish. |
| Model digest mismatch | Keep the request held. Report the public tag/version/digest; do not disable pinning or substitute another model. |
| Gitleaks missing | Install it, check `gitleaks version`, and ensure it is on the launcher's PATH. |
| Docker unavailable | Open Docker and wait for its engine, or choose privacy-only mode. |
| Verifier image absent | Normal `start` builds it. Image preparation needs network once. |
| Port already in use | Stop your owned instance or choose `start --port 8766`; open the printed URL. The launcher never replaces an unknown process. |
| Another launcher is active | Wait for its setup/download to finish; do not start a duplicate. |
| Clipboard unsupported | Use a supported macOS/Windows desktop session and rerun platform setup. Linux capture is unsupported. |
| Clipboard has no new preview | Enable consent, then copy new text. Pending checks need time; held/expired copies have a marker and cannot be copied as approved text. |
| Repair produces no new patch | Check readiness, named test, paused state and result reason. An already repaired demo may now pass its baseline. Existing edits are never reset automatically. |
| Browser asks to connect again | Reconnect after backend restart/session expiry, then explicitly re-enable desired capture/watchers. |

The managed stdin helper currently uses the default port 8765. Non-default ports can use the browser or explicitly configured client integration; do not assume token discovery changes the helper endpoint.

## Update and uninstall

Stop the owned backend first. Source install: review the changes, `git pull --ff-only`, rerun `./scripts/setup.sh`, then start. Wheel install: activate its virtualenv and install the newer reviewed wheel with the same extras. Runtime data stays separate; no source edits or demo copies are reset.

To uninstall, stop DevGuard, then remove its virtualenv/checkout when no longer needed. Runtime data and external Ollama models/Docker images are separate; inspect and remove only your own unneeded data. DevGuard does not delete them automatically. Never upload runtime logs, tokens, databases or clipboard text in a support request.
