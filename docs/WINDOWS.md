# Windows setup and support

Windows native support is being validated for v0.3.0. Python 3.11/3.12 on Windows 11 x64 is the intended user configuration. GitHub Windows runners check native API behavior; they do not establish real-Gemma performance or physical Windows 11 desktop reliability. Windows ARM, network/removable source volumes and Windows services/session-zero capture are not supported targets.

## Install and run

Install Python 3.12 from [python.org](https://www.python.org/downloads/windows/), [Git](https://git-scm.com/downloads/win), [Ollama](https://ollama.com/download/windows) and [Gitleaks](https://github.com/gitleaks/gitleaks#installing). Keep `python`, `ollama` and `gitleaks` on your user PATH. For repairs install [Docker Desktop with its WSL 2 backend](https://docs.docker.com/desktop/setup/install/windows-install/) and select **Linux containers**. Do not install a separate DevGuard instance inside WSL for native Windows clipboard capture.

In PowerShell, in a local NTFS checkout (avoid OneDrive junctions and network shares):

```powershell
git clone https://github.com/Abhijan-Patra/DevGuard.git
cd DevGuard
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup.ps1
.\.venv\Scripts\python.exe -m devguard doctor --privacy-only
```

The command-scoped execution policy permits the reviewed repository script for that process only; it does not change machine or user execution policy. Alternatively review/run the same commands manually. Activation and administrator privileges are unnecessary.

Open Ollama and Docker Desktop; leave their services running. The launcher downloads only the exact pinned model if absent. A missing dependency or different model digest holds startup. Start the full workspace:

```powershell
.\.venv\Scripts\python.exe -m devguard start
.\.venv\Scripts\python.exe -m devguard status
.\.venv\Scripts\python.exe -m devguard stop
```

Use `start --privacy-only` if Docker is not installed; repairs are then unavailable. `doctor` checks Docker and its prepared image; before the first start a missing verifier image is expected. Open `http://127.0.0.1:8765/app` and select **Connect this browser**. The dashboard is the same on Windows and macOS.

## What runs locally

- The pinned `gemma4:e4b-it-q4_K_M` model through local Ollama, credential scanning, context gate and memory-only composer.
- Explicitly enabled **CF_UNICODETEXT** clipboard observation; capture starts OFF, existing text is skipped, bounds and source sequence are checked. Cleaned text requires a separate version-bound copy action. Sensitive held text displays a placeholder, never the original. Busy clipboards retry. Images, screenshots, recordings and keystrokes are not collected.
- Source investigation, opt-in saved-file monitoring, Docker verification and reviewed single-file apply/rollback for enrolled small Python projects. Trusted tests and model authority remain unchanged.
- An owned detached backend. Stop verifies PID creation time and exact argv, then signals a private event for graceful worker shutdown. It never treats Windows SIGTERM as a graceful signal or kills Docker/Ollama/unrelated programs.
- Runtime files with checked Windows ACLs (operator, SYSTEM and administrators); POSIX chmod is not treated as Windows protection. Reparse/junction/alternate-stream/device paths and multiple source hard links are denied. Parent handles and final handle-name checks reject directory substitution during reads/writes. Local administrators and same-user malicious software remain outside the isolation boundary.

No setup step changes global coding-client configuration or pretrusts hooks. Managed MCP configuration is generated with Windows quoting, but Windows Codex/Claude signed-in hook/transport workflows need separate trials; historical Mac CLI evidence does not prove those paths.

## Troubleshooting

| Symptom | Action |
|---|---|
| Python opens Microsoft Store | Install Python from python.org, reopen PowerShell, check `python --version`. |
| Gitleaks unavailable | Install its official Windows binary, add its directory to your user PATH, reopen PowerShell. |
| Ollama unavailable | Open Ollama, or run `ollama serve` in a separate terminal if no server is active. |
| Docker unavailable | Open Docker Desktop, complete WSL 2 setup and switch to Linux containers, or use privacy-only mode. |
| Private ACL/path held | Use a local user-owned NTFS directory; do not weaken ACLs or use network/OneDrive junctions. A prior shared runtime directory should be preserved and a fresh `DEVGUARD_HOME` selected. |
| Clipboard unsupported or inaccessible | Use a signed-in Windows desktop session with the installed dependencies. Remote clipboard redirection and clipboard-history/cloud-sync settings are OS features outside DevGuard. |
| Already running / port occupied | Run `status`; use `stop` for the owned backend. Choose `--port 8766` for another service; do not kill arbitrary processes. |
| Stale patch/copy | Reinspect the new source/copy. Concurrent changes are deliberately preserved. |

A passing test is evidence for that test only. No perfect detection, universal paste interception, every-bug repair or production certification is claimed.

Startup loads the digest-checked local model without a prompt before accepting private work. This reduces first-request cold-load holds; later resource contention or model eviction can still result in a held inspection. The backend's final scan and source/version checks remain mandatory.
