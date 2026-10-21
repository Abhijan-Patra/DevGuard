DevGuard is a local privacy guard and reviewed backend repair workspace for AI-assisted development. This public preview includes an installable wheel, source distribution, checksums and a source setup script.

Start with the [installation guide](https://github.com/Abhijan-Patra/DevGuard/blob/main/docs/INSTALL.md). Install Python 3.11/3.12, Ollama, Gitleaks and Docker for repairs. The pinned local Gemma model is downloaded separately; model weights and user data are never bundled.

- Context inspection and sanitized clipboard previews preserve useful debugging text and replace detected values with placeholders.
- A local browser workspace provides managed source reads, explicit cleaned-copy/composer actions, scoped monitoring, repair review, approved apply/rollback and redacted activity.
- `devguard doctor` explains missing prerequisites. `devguard start --privacy-only` runs without Docker.
- The wheel includes its public repair demo, independent tests and minimal Docker build files, and keeps mutable data outside installed package files.
- Capture and source watchers start OFF; repair starts paused. Your project is never enrolled automatically.

Clean installation checks run on macOS/Linux with Python 3.11/3.12. A separate recorded Apple silicon trial used real pinned Gemma and Docker and exercised a verified repair, disposable apply and rollback. CI package tests are not physical clipboard/model-performance proof. See the [release checklist/evidence](https://github.com/Abhijan-Patra/DevGuard/blob/main/docs/RELEASE_CHECKLIST.md).

**Preview limits:** native clipboard is macOS-only; repair supports small enrolled Python projects with named independent pytest checks and one changed source file per candidate. Clipboard observation cannot block every paste. Classification may miss data or hold benign text. The public website is a read-only tour, not a remotely hosted local agent. Do not expose operator controls to the internet.

The wheel is distributed here on GitHub, not on PyPI. Use the supplied SHA256SUMS to check downloads. Original code is MIT; external tools and model weights retain their own licences. [Support](https://github.com/Abhijan-Patra/DevGuard/blob/main/SUPPORT.md) · [Security reporting](https://github.com/Abhijan-Patra/DevGuard/blob/main/SECURITY.md).
