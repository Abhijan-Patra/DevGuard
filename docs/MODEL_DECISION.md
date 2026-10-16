# Model decision: one Gemma 4 E4B

Decision date: 16 October 2026. Selected for implementation; not benchmarked by this project.

## Selection

Use local instruction-tuned Gemma 4 E4B via Ollama, pinned for setup to `gemma4:e4b-it-q4_K_M`. This is the explicit Q4 version of the selected E4B, not a change of model family. The generic `gemma4:e4b` tag selected a larger MLX download on the first Mac; the explicit tag avoids that backend-dependent choice. The official model card documents Apache-2.0 licensing, coding and native function calling. These support a trial; they do not establish task accuracy or runtime fit.

Keep one resident model and sequential task prompts:

| Task | Model contribution | Code outside model authority |
|---|---|---|
| Clipboard/text privacy | Contextual confidentiality and proposed redaction spans | Capture consent, exact span validation, detector findings, final release |
| Context minimisation | Explain what information the stated task requires | Size bounds and policy; hold if useful facts would be lost |
| Investigation | Select allowed evidence tools and interpret observations | Path restrictions, tool execution, budgets and isolation |
| Repair | Propose a minimal source patch and revise using test feedback | Verifier, expected outcomes, original-source apply |
| Report | Concise evidence-grounded explanation | Export scan and supported-coverage labels |

Do not assign different models to teammates or assume a larger model fixes policy/tool problems. Codex/Antigravity are development assistants, not hidden runtime fallbacks.

## Why this choice

It aligns the runtime with the Gemma track, allows local processing and avoids managing several model packages. Qwen3.5-4B remains a credible alternative, but we have no project measurements proving either model universally superior. Earlier Qwen-first instructions are superseded. Do not promise E4B can diagnose every bug or detect every sensitive detail.

E4B denotes effective parameters; it is not a four-billion-total-parameter memory budget. Google lists roughly 8B total including embeddings. Ollama currently lists backend-dependent E4B artefacts around 6.6–9.5 GB; package bytes are not runtime RAM. Confirm the selected backend and digest, and measure macOS memory pressure with the IDE and worker running.

## Trial before implementation depends on it

1. Start Ollama and pull the selected tag. Do not download other models concurrently.
2. Record Ollama version, backend, model digest, quantisation, context, output cap, thinking setting and hardware.
3. Start at about 4,096 context tokens, one request and a bounded output; follow runtime-supported tool schemas.
4. Evaluate benign text, a detector-matching synthetic secret, unseen confidential prose and irrelevant context with a supplied task.
5. Make real file/test tool calls and propose a patch on three independent tiny backend variants.
6. Run trusted tests and record successes, malformed arguments, missed sensitive spans, elapsed time and memory pressure. Include loading time separately.
7. Approve readiness only from actual outcomes. A target is several complete trials within the chosen job budget; do not publish a success percentage from hypothetical outcomes.

Fast detector findings cannot be downgraded by Gemma. Reject invalid offsets, unsupported actions and truncated JSON. Treat source/log instructions as data. Never render hidden reasoning; show selected tools, concise explanations and evidence references.

## Contingency without model sprawl

First shorten evidence, correct tool templates, bound output and move independent test execution to the other Mac. If the selected model still cannot run acceptably, record the failed trial and explicitly revise the decision with the team. A short GPU trial can run the same E4B package after capacity checks. A hosted Gemma API variant is a separate model/deployment decision with different data handling and quota; it is not an automatic fallback.

Setup has begun. Ollama client/server 0.40.4 respond locally; no model is currently loaded. The selected E4B Q4 download is in progress. Compatibility and inference/tool behaviour remain unverified until the download finishes and the smoke test runs.

## Sources

- [Google Gemma 4 model card](https://ai.google.dev/gemma/docs/core/model_card_4)
- [Ollama Gemma 4 E4B package](https://ollama.com/library/gemma4:e4b)
- [Ollama context and unloading controls](https://docs.ollama.com/faq)

Sources checked 16 October 2026. Model selection and trial requirements are project recommendations, not organiser requirements or comparative benchmark conclusions.
