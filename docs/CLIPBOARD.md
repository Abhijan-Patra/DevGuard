# Required clipboard capture: optimised text workflow

Owner: Mac 1. Presentation: Windows 1. Evaluation cases: Windows 2; backend assertions: Mac owners.

Clipboard capture is explicitly required. It must not be removed merely because backend bug fixing does not use screenshots. This feature is separate from screen capture and does not depend on screenshots, recordings or keyboard monitoring.

## Capture scope and consent

- Disabled until the developer enables text clipboard protection for the selected session.
- Observe only the enrolled host's system text clipboard. Do not enumerate clipboard history, copy images or inspect every app window.
- Disabling capture stops reads, cancels queued analysis and clears transient originals/maps. Ordinary app shutdown also clears them.
- Explain that copied text may belong to a different application; keep analysis on the configured trusted host and do not attach content to a project solely because that project is selected.
- Clipboard APIs can create OS permission prompts. Respect denial and show ERROR/UNSUPPORTED; never bypass permissions.

## Efficient initial macOS implementation

Use a native `NSPasteboard` adapter. macOS provides a change counter; start with an adjustable approximately 750 ms check of the counter, reading text only when it changes. This is a polling implementation, not a claim of universal native change notifications. Measure actual CPU use and tune. Do not invoke Gemma on each poll.

On a new copy:

1. Assign a monotonically increasing content version; cancel older queued work.
2. Check clipboard type/size before processing. Start at a 32 KiB text budget. Oversized or non-text items get SKIPPED and an explicit unsupported status; never truncate silently and declare safe.
3. Compute a session-keyed digest for duplicate detection; run fast detectors locally.
4. Block high-confidence credential release independently of model opinion. Produce a redacted finding without echoing the match.
5. Queue Gemma only if contextual sensitivity needs analysis or an explicit task allows relevance analysis. Debounce rapid changes, for example 250 ms, and keep only the latest pending copy.
6. Validate model output and offsets against the exact immutable version. If the clipboard changed, discard the result instead of applying it to new content.
7. Emit redacted status and a cleaned preview where supported. Do not automatically replace the clipboard.

Initial raw-text lifetime target: no more than 60 seconds and no longer than needed for the decision; clear immediately on disable/session end. Decision-cache target: five minutes, session memory only. These are implementation targets to validate, not measured guarantees of OS/process memory erasure. Never persist raw originals or reversible maps.

## States

`OFF`, `CHECKING`, `SENSITIVE`, `REVIEW`, `CLEAR_FOR_CAPTURE_SCOPE`, `SKIPPED`, `ERROR`.

Expose current version, capture host, supported scope and last redacted finding. No stale state may be presented as describing a new copy. CLEAR_FOR_CAPTURE_SCOPE means no issue detected in that inspected text; it is not proof that all sensitive data is absent or that a paste was intercepted.

## Cleaned-copy and guarded-send actions

**Copy cleaned text** is explicit. It verifies expected clipboard version, copies the validated cleaned bytes, records only metadata and suppresses the watcher's own resulting change event. Reject version mismatch with a conflict and leave new content alone. Avoid an unbounded self-scan loop.

**Guarded send** is a separate synchronous operation. Recheck content, task, destination and policy before delivering. If inspection is still pending, hold it. Unknown task means confidentiality checking only; do not guess relevance. Failure/timeout means REVIEW or BLOCK through the supported route.

Changing the clipboard after the user pasted does not retract anything. An unrelated app can paste before detection or read its own file directly; capture alone cannot prevent that. Claim prevention only for the actual gate/adapter paths tested.

## Coverage for this build

macOS text capture is the first native implementation. Windows dashboard development does not imply a native Windows capture adapter. Show unsupported capture hosts explicitly; a second OS implementation is additional backend work for the Mac owners to review.

## Acceptance cases

- Capture OFF performs no clipboard reads after disable completes.
- Repeated unchanged counter values produce no text reads/model calls; duplicate content avoids repeated model work within policy/task scope.
- Copy A, then B while A is analysing: A cannot overwrite B's status or clipboard.
- Copy cleaned text triggers no infinite loop and does not replace newer content.
- Large/binary clipboard item shows SKIPPED, not safe.
- Secret match is absent from audit/error logs and model-bound cloud evidence.
- Model crash/pending state cannot release through guarded send.
- Benign code remains useful; no raw history is exported.
- Record polling CPU cost and copy-to-finding latency on actual hardware; include misses and false positives.
