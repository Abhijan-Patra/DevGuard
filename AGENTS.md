# DevGuard repository instructions

## Current scope

This repository began as a planning/handoff package. A first authenticated readiness API and local Ollama adapter now exist; privacy enforcement, native clipboard capture and repair remain unimplemented. README and docs/FINAL_PLAN.md are the product direction. Earlier external Qwen-first/screen-capture proposals are superseded.

## Fixed decisions

- One runtime model: local Gemma 4 E4B through Ollama, using explicit Q4 tag `gemma4:e4b-it-q4_K_M`; validate in a real trial and pin digest/settings after download.
- Privacy protection and optimised opt-in text clipboard capture are required. Clipboard capture must not be removed when excluding visual bug diagnosis.
- Backend investigation uses source, diffs, selected structured logs, named API probes and independent tests. No screenshot, screen-recording or keyboard-monitoring dependencies.
- Rules enforce policy; the model proposes classifications/actions. No fixture-specific secret answers, scripted successful repairs or fabricated results.
- Clipboard observation alone does not prevent every paste. Supported gates must inspect before delivery and hold on unresolved checks.
- All backend/model/security/repair/native-capture logic belongs to Mac 1 and Mac 2. Windows 1 owns UI; Windows 2 owns scenario content/manual QA/demo docs. Follow docs/TEAM_WORKFLOW.md and task-file paths.

## Collaboration

Read your task file and docs/API_CONTRACT.md before coding. Work in a separate clone/assigned codex branch. Coordinate shared-schema/dependency changes with Mac 1. Preserve other owners' files and user edits. The initial documentation publisher may create the shared planning package; subsequent implementation follows ownership.

## Privacy and authority

Never log or commit raw secrets, private clipboard content, reversible maps, access tokens, personal logs, databases, snapshots or model weights. Do not send real private input to development assistants for debugging. Use declared synthetic fixtures.

The model cannot change policy, trusted tests, expected outcomes or original-source apply authority. Restrict tools and paths; reject traversal/symlink escapes. Sandboxed tests use prepared dependencies and dummy data. Enforce bounds and final source-hash checks. Review docs/SECURITY_POLICY.md for details.

## Verification and claims

Document installed client/model/runtime versions and actual supported paths. Label fixtures, unrun checks, unsupported capture hosts and unverified integrations. Do not claim universal interception, perfect detection, every-bug repair or production recovery. Show tools, evidence and concise explanations, not hidden reasoning/confidence gauges.

For code changes run focused meaningful checks; for this docs-only package validate links/consistency and do not invent app results. Use supplied user instructions to resolve scope corrections.
