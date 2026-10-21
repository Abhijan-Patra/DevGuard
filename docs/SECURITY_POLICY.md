# Privacy, permissions and execution policy

Owner: Mac 1 for privacy; Mac 2 for sandbox/apply enforcement. This is a build specification, not a security certification.

## Threat model

Developer accidentally sends too much context; an assistant reads private resources through supported tools; source/log text tries to change the guard's instructions; generated patches or logs echo sensitive values. The selected project and model output are untrusted. A separately unrestricted desktop application is outside this enforcement boundary.

Raw private input must be analysed on the enrolled trusted local host. If two Macs are enrolled, disclose that trusted-network topology. DigitalOcean and development assistants receive no real clipboard/private inputs as debugging material.

## Policy before model opinion

Trusted configuration defines allowed source roots, protected resources, named tools/tests and destinations. Canonicalise paths and symlinks, reject traversal and verify content versions. No secret-looking string is tested against a provider. Credentials remain protected even when Gemma calls them fixtures or harmless.

The model proposes sensitivity, exact spans and task relevance. Invalid offsets, malformed JSON, exhausted budget or unavailable model produce a held request. A confidence number is not permission. Explicitly declared synthetic fixtures are for tests only; there is no runtime special-case allowlist keyed to demo answers.

For relevance redaction, preserve syntax, data shapes and diagnostic facts. Do not silently remove necessary information or alter a reproduction. If uncertain, hold for local review rather than inventing facts.

## Decisions and release

- ALLOW: release only the inspected bytes to the bound supported destination.
- SANITIZE: validate replacements and re-scan the cleaned bytes before release.
- LOCAL_ONLY: no external destination may receive this content.
- REVIEW: hold; user can revise input or choose an explicitly permitted local workflow. Review cannot bypass hard policy.
- BLOCK: deny; show a redacted reason.

Authorisation binds immutable payload, task, policy revision, destination, expiry and content version. Replays or changed content fail. Review is not an automatic future exemption. Tool/result and prompt adapters must be synchronous to prevent their supported event; asynchronous alerts are advisory.

## Storage and APIs

Audit stores contain metadata, redacted explanations and safe excerpts only. Disable HTTP body logging and model prompt/response dumps. Do not echo sensitive values in hook stdout/stderr, exceptions, UI, exported diffs or telemetry. Clipboard and redaction maps are bounded, memory-only and expiring.

Bind control API and Ollama to loopback initially. Privileged APIs require an unpredictable session token and explicit local operator context. Restrict browser origins; do not use wildcard CORS. Separate operator and adapter scopes: an adapter can evaluate/deliver through its permitted route, not apply a repair. Never give the model an operator token.

## Repair isolation

Export approved files and dummy data to a disposable snapshot. No personal directories, real credentials, privileged container, host networking or Docker socket. Use a non-root user, fixed image/dependencies, filesystem scope and CPU/memory/process/time limits. External network denied; internal demo network configured explicitly if needed.

The model can edit approved application source only. Trusted tests, policy, tool definitions and expected outcomes are mounted outside writable source. Shell string filtering is not isolation. Run fixed named commands. API probes use configured targets, not arbitrary model URLs.

Scan all model-bound tool results and exported artefacts. Prompt-injection text in source/logs cannot grant permissions or disable scans. Retry budgets: initially one job, about eight tool steps and two patch attempts, with measured wall-clock limits.

## Applying a candidate

UI requests operator review/application. Backend rechecks all affected original-file hashes under a lock, validates allowed paths and candidate hash, rejects symlinks/conflicts and applies idempotently. Never overwrite concurrent edits or reset the repository. Preserve rollback metadata without leaking sensitive original content into public reports.

Passing tests establish only the behaviour actually checked. Unresolved or blocked is an acceptable honest outcome.

## Calibrated context policy and managed clients

Confidential facts require explicit review; the model cannot authorize their automatic release by marking them removable. Detected imperative attempts to override privacy/security instructions block. That narrow deterministic pattern is defense in depth and can have misses or false positives; model inspection and fixed tool authority still apply. Programming identifier formats and public digest constants are not personal data solely because they look unique. Actual credential assignments/provider-shaped values remain protected regardless of claims that they are examples. Personal email detection includes sentence-final punctuation.

The scoped client endpoint performs the full inspection/final scan/source check before returning text. A native PostToolUse warning is not the managed source boundary. Treat source text as untrusted instructions even after privacy inspection. Only the two enrolled MCP tool names are enabled in the restricted profile; user-modifiable hook/server configurations are not enterprise enforcement. No change grants original-source apply authority to a coding assistant.
