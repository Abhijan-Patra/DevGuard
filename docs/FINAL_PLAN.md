# Final proposed plan

Revision: 16 October 2026. Proposal only; supersedes earlier Qwen-first and screenshot/recording suggestions. Names and roles are working labels.

## 1. Product

DevGuard helps developers avoid sharing unnecessary or sensitive information with AI coding tools and prepares verified repairs for reproducible backend bugs.

The connected capabilities are:

1. **ShadowLeak:** inspect supported prompts, tool results, selected source and clipboard text; return permitted context, redactions, review or a block.
2. **ShipFix:** investigate failures from backend evidence, propose source changes in an isolated copy and verify meaningful behaviour independently.
3. **Access enforcement:** validate paths, destinations, tool arguments and final patch application outside model authority.

Clipboard capture is required and optimised. Screen capture, screen recording, visual bug diagnosis and keyboard monitoring are outside this implementation. The clipboard watcher collects text only while explicitly enabled; it does not capture copied images.

## 2. Fixed model choice

Use **Gemma 4 E4B through Ollama**, initially `gemma4:e4b-it-q4_K_M`, for contextual privacy analysis, task relevance, bounded investigation and patch proposals. Use separate structured task prompts and one inference queue; do not run multiple specialist models. Rules and tests remain ordinary code.

This selection prioritises the Gemma event track, local processing and integration simplicity. No project-specific comparison proves it best for all tasks. Complete the [model trial](MODEL_DECISION.md) before committing to performance claims. Do not silently switch to Qwen or a hosted model when a task fails.

## 3. Priorities

| Priority | Deliverable | Evidence required |
|---|---|---|
| P0 | Actual guarded prompt/tool evidence pipeline | A detected synthetic secret is absent from the payload actually delivered through that path |
| P0 | Contextual Gemma analysis | Unseen confidential text and irrelevant context receive a validated decision; no canned answer lookup |
| P0 | Optimised clipboard capture | Explicit enable/disable, text change detection, fast scan, bounded model work, pending/stale states and cleaned-copy action |
| P0 | Local audit dashboard and coverage | Backend-derived decisions; fixture/live modes clearly distinct; raw sensitive values absent |
| P0 | One client adapter trial | Real supported prompt or tool interception tested; ship claims limited to verified paths |
| P1 | Isolated backend repair | Baseline fails, genuine model patch passes unchanged independent checks, original source untouched |
| P1 | Review, stale protection and cancellation | New edits reject old candidates; model cannot apply to developer files |
| P1 | Saved-file watcher and idle/on-demand queue | Events deduplicate; foreground guard work takes priority |
| P2 | Extra bug types, automatic idle heuristics, commit gate | Add only after P0 and first P1 loop are stable |

If time is short, ship the working privacy/clipboard path and explicitly label repair incomplete. Do not trade the primary privacy feature for more repair examples.

## 4. Privacy flow

Trusted adapter metadata -> path/destination checks -> fast credential detector -> local Gemma context analysis where necessary -> validated action -> final output scan -> release through the supported adapter.

Sensitivity and relevance are separate. Code can be necessary but confidential; unrelated benign context can be omitted only when doing so preserves the task. Gemma proposes spans with exact offsets; code validates offsets against the original immutable text. Invalid/truncated/uncertain results hold the request. High-confidence credential findings cannot be downgraded by model opinion. No external credential validation calls.

Use `ALLOW`, `SANITIZE`, `LOCAL_ONLY`, `REVIEW`, `BLOCK`. `LOCAL_ONLY` cannot release to a cloud client. Review does not automatically override a protected path or credential block. Hook limitations may require blocking and offering a cleaned prompt for resubmission rather than rewriting the original in place.

Store redacted evidence only. Clipboard originals and placeholder maps are session-scoped, memory-only and short lived. Do not show raw originals in the audit panel. Recheck content and destination immediately before delivery. A warning after copying is distinct from verified pre-delivery prevention.

## 5. Clipboard experience

Developer enables the local text watcher. Detect clipboard changes cheaply; scan only new bounded text. Fast checks produce an immediate observed state, not an unmeasured latency promise. Gemma handles ambiguous confidentiality; relevance analysis additionally requires an explicit task. Without a task, do not guess that content is unnecessary.

Show CHECKING, SENSITIVE, REVIEW, CLEAR_FOR_CAPTURE_SCOPE, SKIPPED or ERROR with a content version and redacted explanation. CLEAR_FOR_CAPTURE_SCOPE is not a guarantee of safe sharing or evidence that a paste was intercepted. Only an explicit guarded send can release text. Offer **Copy cleaned text**, recheck the current clipboard version and suppress the watcher's own write. No silent clipboard replacement, raw history or repeated model calls for the same version.

Mac 1 implements the native capture service. Windows members build UI/specifications; native Windows capture is later backend work unless a Mac owner has time to implement and verify it. A cross-platform dashboard does not imply cross-platform OS capture support.

## 6. Backend repair

Failure signals are named pytest checks, API contract probes, selected structured exceptions and developer reproduction reports. Capture source hashes and a bounded Git diff; no screenshots or recordings.

Create a disposable snapshot including relevant saved uncommitted edits. Reproduce with trusted tests. Feed sanitised source and logs to the same Gemma model using typed tools. Validate and apply proposals only inside the copy. Run the same protected verifier and scan exports. Return READY_FOR_REVIEW, UNRESOLVED, BLOCKED, CANCELED or OBSOLETE.

Initial bug classes: missing/null-input handling and a small incorrect calculation or response contract. Port mismatch, idempotency and credential refactoring are later examples, not promised universal repair support. Tests assert business behaviour, not only HTTP 200. Model-generated tests supplement the independent oracle.

Final application requires explicit local review plus a locked source-hash recheck and conflict rejection. Store a reversible original patch; never reset the user's working tree.

## 7. Four-member allocation

| Member | Main ownership | First deliverable |
|---|---|---|
| Mac 1 / Abhijan / Codex | Schemas, API/auth, guard, Gemma queue, clipboard OS service, redacted store | API contract implementation, model trial and guarded text decision |
| Mac 2 / Codex | Client hooks, worker/scheduler, snapshots, sandbox, independent verifier and patch lifecycle | One adapter interception plus a reproducible failing backend test |
| Windows 1 / Antigravity | Streamlit dashboard and display-only API client | Screens rendering labelled fixture events and clipboard states |
| Windows 2 / Antigravity | Synthetic case specifications, mock content, manual QA, runbook and submission wording | Case catalogue and expected-outcome matrix |

Backend and complex execution decisions belong to the two Mac owners. Assignment is based on requested ownership, not claims about any coding assistant's intelligence. The Windows contributors own meaningful parallel deliverables and need no local model or Docker setup.

## 8. Deployment and resources

Develop independently in four clones. Aim for one local Mac presentation if measured resources permit. If the model and worker are split across the two Macs, explicitly enrol the trusted second Mac and use authenticated SSH tunnels. This is processing within a trusted local network, not strictly single-device processing. No raw privacy input goes to a second machine without configured consent.

One Gemma request at a time; start near 4K context, bounded output and small excerpts. Do not copy the old Qwen 5–7 GB memory estimate onto Gemma. Start Docker around two CPUs and 2 GiB and adjust from measurements. Separate Macs do not pool RAM. Keep 20–30 GB free initially and check exact selected artefacts.

Use the $30 DigitalOcean budget only after a measured need. Optional CPU demo hosting and a short same-model GPU trial are in [setup/budget](SETUP_AND_BUDGET.md). Neither is required for the first milestone.

## 9. Build order

1. Mac owners agree schemas, ownership, policy and capabilities; Windows owners start against examples.
2. Model smoke/tool trial and synchronous guard release on real content.
3. Clipboard capture, versioning, deduplication and explicit cleaned-copy flow.
4. One client hook path and real outgoing-payload evidence.
5. First isolated backend repair; dashboard switches from fixtures to live data.
6. Negative tests, stale rejection, privacy leakage checks, resource measurement and rehearsal.

Reserve the final hour before the supplied 6:30 PM IST submission deadline for freeze, evaluation and submission; do not treat an old screenshot's countdown as live time. Schedule is a planning target, not a delivery guarantee.

## 10. Definition of ready

The privacy demonstration shows real capture/input, actual local Gemma decisions, deterministic enforcement and the actual supported delivered payload. The backend demonstration shows an independent failing test becoming green due to a real candidate source change, with unchanged originals until reviewed.

Report observed successes, misses and unsupported paths. No prewritten successful patches, special-case fixture answers, invented detection percentages, model confidence gauges or universal leak-prevention/production-recovery claims.

References: [model decision](MODEL_DECISION.md), [coverage](COVERAGE.md), [evaluation](EVALUATION.md), [sources](../THIRD_PARTY_NOTICES.md).
