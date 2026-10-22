# DevGuard v0.3.2 — Installed demo verifier

Prepare an exact copy of the bundled independent demo checks in the private runtime, outside model-writable source. Docker Desktop need not mount a package/virtualenv directory that it cannot see. Existing edited test copies hold startup without overwrite; original bundled tests and model/test authority are unchanged. Named checks, source hashes, review, sandbox restrictions and fail-closed behavior remain mandatory.

The v0.3.0 downloaded-wheel hold was isolated to the independent-check bind mount: the source mount existed and worked, but Docker reported the package check directory as nonexistent. Normal/restrictive file-mode diagnostics both produced the expected failing baseline with shared source-checkout checks. The fix changes the prepared demo mount location, not the oracle or filesystem permissions of user files.

# DevGuard v0.3.1 — Windows verifier compatibility

Preserve Windows `SYSTEMROOT` regardless of environment-key casing, plus the user temporary directories, in the Docker CLI's restricted child environment. Private assistant tokens and unrelated variables remain excluded. This avoids losing OS variables required by Windows child processes. Native Windows checks and six clean-wheel platform/version checks remain required for publication.

The published v0.3.0 download matched its checksum and passed real local privacy delivery, but its repair trial held at Docker baseline ERROR before model investigation. That failed trial is retained separately; a direct synthetic Docker diagnostic returned the expected failing test. No Docker engine root cause or universally successful repair is claimed.

# DevGuard v0.3.0 — Windows native support

Windows source setup, local lifecycle, Unicode clipboard capture, private ACL storage and junction-safe source access now share the browser workspace with macOS. See the [Windows guide](https://github.com/Abhijan-Patra/DevGuard/blob/main/docs/WINDOWS.md). Capture/watchers start OFF and repairs start paused. No model/policy/test authority is expanded.

Windows-native CI tests and clean package installs are required before publication. Physical Windows 11 real-Gemma/Docker performance and signed-in Windows coding-client hook delivery are separate, unverified gates. Historical Mac real-model results remain labelled as Mac measurements. No error-free or production-certification claim is made.

## Previous release evidence

**v0.2.1 introduced the verifier compatibility update, retained in v0.3.0.** Its local image is prepared as a single-platform image under a tag bound to public build inputs. Earlier 0.2.0 dependency holds remain in the recorded evidence; the patch also preserves trial failure metadata.

DevGuard is a local privacy guard and reviewed backend repair workspace for AI-assisted development. This public preview includes an installable wheel, source distribution, checksums and a source setup script.

Start with the [installation guide](https://github.com/Abhijan-Patra/DevGuard/blob/main/docs/INSTALL.md). Install Python 3.11/3.12, Ollama, Gitleaks and Docker for repairs. The pinned local Gemma model is downloaded separately; model weights and user data are never bundled.

- Context inspection and sanitized clipboard previews preserve useful debugging text and replace detected values with placeholders.
- A local browser workspace provides managed source reads, explicit cleaned-copy/composer actions, scoped monitoring, repair review, approved apply/rollback and redacted activity.
- `devguard doctor` explains missing prerequisites. `devguard start --privacy-only` runs without Docker.
- The wheel includes its public repair demo, independent tests and minimal Docker build files, and keeps mutable data outside installed package files.
- Capture and source watchers start OFF; repair starts paused. Your project is never enrolled automatically.

Clean installation checks run on macOS/Linux with Python 3.11/3.12. A separate recorded Apple silicon trial used real pinned Gemma and Docker and exercised a verified repair, disposable apply and rollback. CI package tests are not physical clipboard/model-performance proof. See the [release checklist/evidence](https://github.com/Abhijan-Patra/DevGuard/blob/main/docs/RELEASE_CHECKLIST.md).

**v0.2.x preview limits (historical):** native clipboard was macOS-only; repair supports small enrolled Python projects with named independent pytest checks and one changed source file per candidate. Clipboard observation cannot block every paste. Classification may miss data or hold benign text. The public website is a read-only tour, not a remotely hosted local agent. Do not expose operator controls to the internet.

The wheel is distributed here on GitHub, not on PyPI. Use the supplied SHA256SUMS to check downloads. Original code is MIT; external tools and model weights retain their own licences. [Support](https://github.com/Abhijan-Patra/DevGuard/blob/main/SUPPORT.md) · [Security reporting](https://github.com/Abhijan-Patra/DevGuard/blob/main/SECURITY.md).
