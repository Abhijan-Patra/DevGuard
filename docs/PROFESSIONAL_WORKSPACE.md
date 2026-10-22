# Single-laptop workspace

New users: start with the [public installation guide](INSTALL.md). It covers the source installer, release wheel, prerequisites and troubleshooting. The technical workflows below remain useful after installation.

21 October 2026. One machine owns all former Mac 1, Mac 2 and Windows roles. The primary interface is now the dependency-free browser workspace served by FastAPI at `http://127.0.0.1:8765/app`. The Streamlit dashboard remains available as a legacy interface; the existing Render deployment now hosts a read-only feature tour using the same design and recorded evidence.

## Start and stop

Install official Docker Desktop and Ollama first. From the repository:

```sh
./scripts/devguard-local start
./scripts/devguard-local status
./scripts/devguard-local stop
```

The launcher starts stopped Docker/Ollama applications, downloads only the exact Gemma tag if absent (and refuses duplicate active pulls), validates its fixed digest, builds the verifier only if absent and starts its own detached backend. The only opened port is loopback. Stop targets only the recorded, identified DevGuard process and waits for graceful worker cleanup; Docker, Ollama and unrelated containers are untouched. A sleeping or powered-off laptop does not run jobs.

The launcher registers a disposable copy of the public cart backend at `.devguard/local-demo`, with the original repository tests read-only. It never resets an existing demo copy. A successful applied demo becomes healthy; it should then produce no new repair. To repeat a failure, explicitly enrol another disposable copy rather than reset working edits.

Click **Connect this browser**. This explicit same-origin local pairing creates an eight-hour HttpOnly, SameSite Strict session. No bearer token is exposed to browser JavaScript or placed in URLs/storage. Cookie-authenticated requests require the workspace header, local host and exact origin on mutations. Cross-origin pairing, remote hosts and framing are denied. This assumes a trusted local browser/OS; it does not defend against a malicious process already running as the operator. Use `--no-browser-pairing` for bearer-only deployments.

## Workflows

- **Context gate:** inspect a prompt or structured text; the deterministic scanner, local Gemma and final scan decide whether a cleaned preview is available. Releasing is a separate explicit action to the enrolled local composer. A receipt proves local delivery only. The composer expires after ten minutes and never sends to a cloud assistant.
- **Managed source read:** choose an enrolled source file. The backend reads it through descriptor-anchored path checks and binds its digest to the inspection. All delivery routes recheck this source after final scanning; changed source holds. No unrestricted shell/file access is introduced.
- **Text clipboard:** capture starts OFF. Enable with explicit local consent, then copy new text. The existing clipboard is skipped. Copy cleaned text checks the inspected version. Disable clears transient work. Native macOS/Windows desktop text only, no images/screenshots/keyboard monitoring.
- **Backend repairs:** choose an enrolled project and named check, queue investigation and resume. Observe actual baseline, tools, verification and diff. Apply requires a review dialog, explicit approval and expected candidate/base hashes. Reject/cancel/pause remain available. Rollback is explicit, session-only and refuses any concurrent change in the applied tracked source. Neither application nor rollback resets a repository.
- **Projects:** opt in to saved-file watching for an exact manifest. Changes debounce and deduplicate into queued investigations. Monitoring never silently starts execution. Quiet-time mode optionally admits jobs after a configured period without foreground model work; it is queue-based, not OS-input/keyboard monitoring. Manual pause disables automatic admission.
- **Activity:** paginated, filterable metadata-only audit; explicit export. Loaded-record counts are not overall accuracy/usage statistics.
- **Verification:** recorded real-model, native clipboard, Docker, delivery and rollback experiments, including calibration mismatches; export bounded evidence. These records do not authorize runtime actions.
- **System:** actual readiness, package digest, scope and coverage limits. Missing model/scanner/Docker produces held/unavailable states, never a simulated successful result.

## Enrol a real project

Provide a reviewed JSON file to `./scripts/devguard-local start --projects-config /absolute/path/projects.json` (stop the owned backend first). One to eight projects; up to 32 UTF-8 source files, 128 KiB each and 512 KiB total; one changed source file per candidate. Source needing privacy alteration is held rather than silently changed for repair. The model's context budget is smaller than these filesystem limits: use small focused modules.

```json
{
  "projects": [{
    "project_id": "example-api",
    "root": "/absolute/canonical/project",
    "source_files": ["calculation.py", "main.py"],
    "writable_files": ["calculation.py"],
    "trusted_tests": "/absolute/canonical/independent-checks",
    "test_names": ["calculation"],
    "image_id": "sha256:REPLACE_WITH_ACTUAL_64_HEX_IMAGE_ID"
  }]
}
```

The example is a template, not executable configuration. Each named check resolves to `test_NAME.py` in the independent test directory. Prepare the image with required test dependencies in advance. The worker uses the image ID, no network, fixed pytest command, read-only mounts, non-root UID, dropped capabilities, two CPUs, 1 GiB RAM and bounded time/output. There is no arbitrary URL, shell or test command field. The reviewed manifest stays local; roots are never returned in the UI/audit.

## Managed terminal path

```sh
printf '%s' 'Declared synthetic debugging text' | .venv/bin/python -m devguard.managed --task 'Debug this request' --deliver
.venv/bin/python -m devguard.managed --project demo-cart --path cart.py --deliver
```

These commands emit redacted metadata only; approved text appears in the local composer. They do not install hooks or grant access to unrestricted tools. The two guarded stdio MCP tools and native CLI hooks now have recorded synthetic-receiver trials with real Gemma. See [client integration](CLIENT_INTEGRATION.md) to prepare isolated profiles and explicitly trust native hooks. Signed-in cloud delivery, automatic context, attachments, alternate tools and transcripts remain outside the measured scope.

## Evidence discipline

Automated tests inject declared doubles for policy/control-flow boundaries; real-model and Docker trials are separate. Capture remains off outside explicit clipboard testing. The public project contains bounded redacted evidence only; all runtime files, tokens, prompts, candidates and snapshots stay ignored. No model weights are committed.

Windows setup uses the [PowerShell guide](WINDOWS.md); the Unix shell launch examples above remain valid on macOS/Linux.
