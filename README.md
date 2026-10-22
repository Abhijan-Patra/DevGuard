# DevGuard

**A local privacy guard and reviewed backend repair workspace for AI-assisted development.**

Keep useful debugging context, replace detected sensitive values with placeholders, and review independently tested code changes before applying them. DevGuard uses **local Gemma 4 E4B through Ollama**. Its browser workspace runs on your laptop at `http://127.0.0.1:8765/app`.

[Install guide](docs/INSTALL.md) · [Latest release](https://github.com/Abhijan-Patra/DevGuard/releases/latest) · [Read-only tour](https://devguard-demo.onrender.com) · [Support](SUPPORT.md)

## Get started

This is a **public preview**. The complete local workflow has been exercised on an Apple silicon Mac with 16 GB memory. Native text clipboard adapters exist for macOS and Windows. See [Windows setup and verification scope](docs/WINDOWS.md). Linux native capture is unsupported. Windows hardware/model performance requires a separate real-device trial.

Install **Python 3.11 or 3.12**, [Ollama](https://ollama.com/download), [Gitleaks](https://github.com/gitleaks/gitleaks#installing), and [Docker Desktop](https://docs.docker.com/desktop/setup/install/mac-install/) for repairs. Open Docker and Ollama and finish their own setup first.

```sh
git clone https://github.com/Abhijan-Patra/DevGuard.git
cd DevGuard
./scripts/setup.sh
./scripts/devguard-local start
```

The installer creates a private virtualenv in the checkout; it does not modify your global Python or coding-client configuration. First startup downloads the exact model if needed and builds a small public test image. Both require an internet connection. Later inference and sandbox tests run locally.

Open **http://127.0.0.1:8765/app**, choose **Connect this browser**, then choose a workflow. Clipboard capture and project watching start **OFF**; repairs start **paused**.

```sh
./scripts/devguard-local doctor       # Checks and specific next steps
./scripts/devguard-local status
./scripts/devguard-local stop         # Leaves Docker and Ollama running
```

Only need context inspection and clipboard protection? Use `start --privacy-only`; Docker is not needed. Prefer an installed wheel instead of a checkout? Follow the [release installation steps](docs/INSTALL.md#install-a-release-wheel).

## What you can do

| Workflow | What happens |
|---|---|
| Context gate | Inspect supplied text with deterministic credential rules and local Gemma. Review the approved text before explicitly releasing it to the local composer. |
| Text clipboard | Opt in, then copy new text. Detected values become placeholders such as `[CREDENTIAL_1]`. Held copies show a whole-copy marker. Copying the cleaned version is explicit. |
| Managed source | Read only source files enrolled in a trusted local manifest. Recheck the source hash before delivering the approved bytes. |
| Backend repair | Run a named independent check in restricted Docker, let Gemma investigate approved source, and review a verified patch. Apply and rollback check source hashes and require approval. |
| Project monitoring | Opt in to watching an exact file manifest. Changes queue work; they do not grant permission to execute or apply a repair. |
| Activity and verification | View metadata-only audit events and clearly labelled recorded experiments. Previous evidence is not proof of a new run. |

The default repair project is a **disposable, intentionally buggy cart example**. Your own project is never enrolled automatically. [Enrol your own project](docs/PROFESSIONAL_WORKSPACE.md#enrol-a-real-project) when you have reviewed its source scope and independent tests. Repair currently targets small Python projects with fixed named pytest checks and one changed source file per candidate.

## Privacy and limits

DevGuard does not use screenshots, screen recordings or keyboard monitoring. Inputs are processed by the pinned local model; no cloud assistant receives them through the default composer. Audit retains bounded redacted metadata. Clipboard text, previews and candidates remain transient.

Clipboard observation cannot prevent every paste. The guard enforces only its supported synchronous gates and enrolled source tools; an unrestricted assistant can still use other paths. Model classifications can miss sensitive data or hold benign text, and a passing test checks only the behavior covered by that test. No perfect detection or every-bug repair claim is made.

[Client integration and limits](docs/CLIENT_INTEGRATION.md) · [Privacy policy](docs/SECURITY_POLICY.md) · [Report a vulnerability](SECURITY.md)

## Verification and development

The release pipeline runs the regression suite, dependency checks, JavaScript syntax checks, builds a wheel/source distribution, and tests a clean wheel installation outside the checkout. Packaged demo source and independent tests are checked against the reviewed originals. Native clipboard and live Gemma/Docker experiments are recorded separately from CI doubles.

[Release verification](docs/RELEASE_CHECKLIST.md) · [Measured evidence](docs/PROFESSIONAL_STATUS.md) · [Architecture](docs/ARCHITECTURE.md) · [API contract](docs/API_CONTRACT.md) · [Contributing](CONTRIBUTING.md) · [Changelog](CHANGELOG.md)

MIT for original project code. Gemma and external dependencies keep their own licences. No model weights, credentials or user data are included. See [third-party notices](THIRD_PARTY_NOTICES.md).

Windows users: follow the [PowerShell installation guide](docs/WINDOWS.md). Runtime starts with capture/watchers OFF and repairs paused on every supported platform.
