# DevGuard — submission text for team review

**Categories:** Open-Source AI Project and Best Use of Gemma 4, as allowed by the organiser's latest clarification. Confirm the final submission form's category options.

**Repository:** <https://github.com/Abhijan-Patra/DevGuard>

**License:** MIT for the application; Gemma weights and third-party dependencies retain their own terms. No hosted proprietary model is required for the measured workflows. Add an actual recording link only if one is created and required; no video link is claimed here.

## What we built

DevGuard is a local developer privacy guard and backend repair agent using Gemma 4 E4B through Ollama. A rule-based credential scanner and the local model inspect submitted text; a managed gate releases only approved, version-bound bytes to a configured receiver. Opt-in macOS text clipboard capture offers a cleaned preview and a version-checked copy action. It starts OFF.

The repair agent investigates an approved backend snapshot through typed tools. It must reproduce a failing baseline inside a restricted Docker container, generate a source patch and pass independent protected tests before presenting a candidate. The model cannot apply to original files or edit policy/tests. Operator application checks candidate/base hashes and idempotency; concurrent edits invalidate the candidate.

## Why Gemma matters

One pinned local model performs semantic sensitivity/relevance analysis and chooses the backend investigation/patch actions. This is not a canned patch catalogue. Foreground privacy overtakes waiting background requests in a bounded shared inference queue; active inference is not preempted. The measured package is `gemma4:e4b-it-q4_K_M`, digest `dc35e8d9c6061baa6f0fa870975ab6932e2542b579b13ea0f199fa4bb7300c9c`, context 4096, privacy/tool output caps 512/1024, temperature 0, thinking off.

## What actually ran

- **209 automated tests passed** on integrated main `1099a86` plus Mac 2 worker; pip check clean. These tests include declared fake model/verifier ports and are separate from real-model measurements. One dependency deprecation warning remains.
- On an M4 Air with 16 GB, real Gemma/guard/API/Docker reproduced the declared cart failure, generated a patch, passed independent verification, applied only to a disposable public copy, repeated application idempotently and passed post-apply tests in **46.07 s**. Original repository source/tests were unchanged; worker stopped; 28 audit records survived reopening.
- A separate genuine candidate followed by a concurrent edit returned **409 STALE_SOURCE**, preserved that edit and became OBSOLETE. Queued cancellation produced no candidate. **42.19 s** for that trial.
- A real local reference receiver received exactly the inspected cleaned bytes; replay was held; all five live dashboard views rendered. **1.282 s** for the single synthetic privacy evaluation on Mac 2. No source apply or clipboard enablement occurred in that check.
- An isolated native Cocoa pasteboard passed all **12** lifecycle/copy checks; **1.550 s** copy-to-finding. A distinct consented system-clipboard combined input was **HELD/REVIEW** and did not exercise cleaned copy; capture was disabled afterward. Both results remain visible.

Evidence: [repair metadata and failures](../devguard/repair/README.md), [Mac 2 native check](../evals/results/mac2-private-pasteboard.json), [Mac 2 live delivery/UI](../evals/results/mac2-live-dashboard.json), and [Mac 1 owner measurements](MAC_1_WINDOWS_1_COMPLETION.md).

## Current limits

The 26 catalogue scenarios remain **UNRUN**; targeted experiments are not a full unseen benchmark. No perfect detection, universal assistant interception or production recovery claim is made. Installed Codex interception remains a prototype/unverified; arbitrary app pastes are outside the managed gate. Windows native clipboard capture, automatic OS-idle scheduling and general production-project enrollment are unfinished. A sleeping laptop cannot keep repairing. A single-file atomic replacement still has a narrow race against unrelated editors.

The dashboard distinguishes Fixture Mode from the actual backend. The standalone mock server is rehearsal data and is not proof of live execution. Original inputs, clipboard text, model prose, tokens and snapshots are not committed; durable audit stores constrained metadata.

## Demo and run

Follow [the live runbook](DEMO_RUNBOOK.md). Start the actual backend with an inspected local verifier image and use the local operator launcher in [integrations](../integrations/README.md). On Mac 2, backend 8766 preserves the existing SSH tunnel on 8765; dashboard is <http://127.0.0.1:8501>.

This document is prepared text for the team's submission. It does not mean a hackathon form, video or deployment has been submitted.
