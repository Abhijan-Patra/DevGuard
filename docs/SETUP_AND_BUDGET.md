# Setup and resource budget

This documentation package does not install dependencies or provide application code. Mac owners add real application start/test commands after implementation and verification. Do not fabricate commands for nonexistent entry points.

## All members

Clone `https://github.com/Abhijan-Patra/DevGuard.git`, read README, AGENTS, shared contract and your task file, then create your assigned branch. Keep personal logins separate. Source-control credentials are not shared service credentials.

## Mac 1

Python 3.12, Git, a compatible Ollama runtime, selected Gemma package and Gitleaks. Python dependency locking is owned here; use uv or venv with a checked-in lock after package selection.

Model trial commands, after Ollama is installed and its server is running:

```sh
ollama --version
ollama pull gemma4:e4b-it-q4_K_M
ollama show gemma4:e4b-it-q4_K_M
ollama run gemma4:e4b-it-q4_K_M
```

Record actual model digest/backend and settings. Package tags may change. The first setup check now confirms the client/server at 0.40.4 with the selected Q4 model downloading. Installed weights and inference performance are still pending. Do not promise that startup is already complete.

For clipboard integration, evaluate a compatible macOS native bridge for NSPasteboard, with consent and permission failure handling. Keep capture platform code separate from classification so the service can be tested with synthetic text.

## Mac 2

Python 3.12, Git, Docker, pytest/HTTPX and Ruff. Own the demo FastAPI application, trusted tests and restricted snapshot worker. Start container limits around two CPUs and 2 GiB, then measure. Do not load another model on this host just for appearance; the same selected E4B may be used sequentially for independent development trials.

Prefer a single-host final run if comfortable. If two Macs are needed, enrol the second host explicitly, use authenticated SSH tunnels and bind service ports locally. Raw privacy material is not sent to an unenrolled host. Windows UI work begins with fixtures and needs neither Docker nor a local model.

## Memory and disk

E4B package sizes vary by backend (currently roughly 6.6–9.5 GB). Runtime memory includes context/cache and other processes; the old Qwen 5–7 GB allowance is not valid evidence for Gemma. Start near 4K context, one request and bounded output. Observe memory pressure with Codex, UI and test runner active. Two 16 GB Macs do not form a 32 GB inference server.

Initially allow 20–30 GB free storage, then adjust from actual model/image/dependency size. Cache prepared dependencies for an offline demonstration. No fine-tuning or distributed inference.

## Windows members

Git and Python sufficient for the planned Streamlit UI and fixture work. Use Antigravity on your owned paths; do not build a second backend or security engine. Mac 1 owns package pins. Windows 2 can prepare scenario/specification files without installing backend dependencies. Do not promise a Windows native clipboard agent merely because the dashboard runs there.

## DigitalOcean

User reports $30 credit. The supplied screenshot showed a $5 signup credit and a payment-method requirement, not proof the separate $30 is redeemed or GPU-eligible. Verify correct team, redemption, expiry and eligible services before resource creation. This task provisions nothing.

Public prices checked 16 October 2026; availability/account eligibility are unknown. Estimates exclude taxes, storage extras and overages.

| Optional resource | Published rate | Example |
|---|---|---|
| Basic regular CPU, 1 vCPU / 2 GiB | $0.01786/hour, $12 monthly cap | 48 hours about $0.86 |
| RTX 4000 Ada, 20 GB GPU / 32 GiB system RAM | $0.76/hour | Eight hours $6.08 |

Start at $0 cloud spend. If needed, use CPU hosting for a synthetic demo service; keep actual private capture and enforcement local. A short GPU trial can test the same E4B after runtime-fit checks. Remote inference is a separate consented hybrid mode and receives only approved sanitised excerpts; detector misses remain possible. Do not move raw clipboard collection to the cloud.

Plan initial spend under $10 and keep about $20 reserve. Alerts are not hard spending caps. Destroy instances after use; power-off continues billing. Review retained billable volumes/snapshots separately.

Sources: [CPU rates](https://www.digitalocean.com/pricing/droplets), [GPU rates](https://www.digitalocean.com/pricing/gpu-droplets), [billing](https://docs.digitalocean.com/products/droplets/details/pricing/), [signup credit](https://docs.digitalocean.com/platform/billing/signup-credit/), [Ollama package](https://ollama.com/library/gemma4:e4b).
