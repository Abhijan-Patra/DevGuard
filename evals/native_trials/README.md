# Reproduce native CLI boundary measurements

These files are **protocol test fixtures**, never an inference provider or repair fallback. They use actual installed native clients, the production DevGuard hook/MCP tool, real local Gemma and a loopback-only synthetic provider receiver. The receiver directs fixed tool calls to test client boundaries; no coding-model intelligence or successful repair is inferred from it. Synthetic marker-presence metadata is logged; real user content must never be supplied here.

Prerequisites: trusted local DevGuard/Gemma/Docker startup, optional client SDK installed, prepared `.devguard/local-projects.json`, ports 8766 and 8899 free. Choose a **new private temporary directory outside the repository**. The prepare command refuses to overwrite one. Example:

```sh
.venv/bin/python -m evals.native_trials.prepare /private/tmp/my-devguard-native-trial
export DEVGUARD_NATIVE_TRIAL_DIR=/private/tmp/my-devguard-native-trial
export DEVGUARD_CODEX_BIN=/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex
.venv/bin/python -m evals.native_trials.guard_server
```

In another terminal with the same `DEVGUARD_NATIVE_TRIAL_DIR`:

```sh
.venv/bin/python -m evals.native_trials.provider
```

Then open the installed Codex CLI using the isolated configuration. Review the three exact hook definitions in `/hooks` and trust them through that native UI. **Do not bypass hook trust.** Exit the review session before running measurements.

```sh
CODEX_HOME="$DEVGUARD_NATIVE_TRIAL_DIR/codex-home" "$DEVGUARD_CODEX_BIN" \
  --no-daemon --no-alt-screen -C "$DEVGUARD_NATIVE_TRIAL_DIR/project"
.venv/bin/python -m evals.native_trials.record_trials
```

The recorder runs cases sequentially; the receiver mode is shared and must not be changed concurrently. It verifies held prompts make zero provider requests, allowed prompts provide a positive control, managed source reaches the provider's next request, detected synthetic source credentials do not, traversal produces a held result, and the native Codex shell hook denies its marker command. Results are written to `native-evidence.json` in the private trial directory. Per-client diagnostic output there contains **synthetic test data only** and is not suitable for Git; committed evidence is redacted metadata.

To test a dependency outage, stop only this trial's guard process with Ctrl-C in its terminal. Run each client with `TRIAL_MODE=text` using `run_codex`/`run_claude` and compare appended hook/provider event counts. Both should record a blocked UserPromptSubmit and no new provider request. A native hook that is skipped/crashed/timed out is a different client-level failure and must not be counted as this check.

Stop the two task-owned trial servers when finished. No global auth, trust or client configuration is modified. The recorded production source-read boundary remains in the server, independently of native hooks. Desktop/IDE variants, automatic context, attachments, transcripts, telemetry and real signed-in cloud delivery remain outside these experiments.
