# Contributing

Read [team workflow](docs/TEAM_WORKFLOW.md), [API contract](docs/API_CONTRACT.md), [policy](docs/SECURITY_POLICY.md) and your task file. The repository currently contains a proposal and handoffs; code paths and commands will be added by their owners.

Use a separate clone and assigned `codex/` branch, small pull requests and clear ownership. Explain changed behaviour, actual verification and remaining gaps. Mac 1 coordinates schemas and integration; both Mac owners review enforcement and trusted verification changes.

Use one runtime model, Gemma 4 E4B. Any proposed change requires recorded evidence and an explicit revision to the model decision. Different task prompts do not require different models.

Clipboard capture is required, opt-in and text-only. Backend diagnosis uses source, logs, diffs, named API probes and tests. Do not add screenshot or recording dependencies. Do not replace real classification or repair with fixture lookup logic.

Do not submit raw private inputs, credentials, clipboard history, model weights, local databases, runtime logs or disposable snapshots. Use synthetic fixtures with declared scope and no external credential-validation calls. Preserve model/dependency licence notices.

Run checks appropriate to the changed slice. Security boundaries require meaningful negative cases; documentation-only changes require link/consistency review, not fabricated application tests. Preserve failing/unrun results honestly.
