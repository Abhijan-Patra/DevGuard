# Getting started: first Mac backend foundation

Ollama is already installed on the first Mac; no reinstall is required. Its loopback API responds as version 0.40.4. The selected model download has started but inference is not verified yet.

## Selected model

```sh
ollama pull gemma4:e4b-it-q4_K_M
```

This is the selected Gemma 4 E4B with explicit Q4 quantisation. Ollama lists about 6.6 GB for this package; the current machine initially selected a larger roughly 9.5 GB MLX package from the generic E4B tag, so that initial attempt was stopped. Do not run both downloads for this setup.

The first Mac's download is already running. Network speed determines completion; the backend can be developed and its boundary tests run meanwhile. Existing unrelated models are left untouched. No paid cloud service is needed.

## Python backend

Python 3.11 is available on the first Mac, and this foundation supports Python 3.11 or later. Use an isolated environment:

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pytest -q
.venv/bin/python -m devguard
```

The server binds only to `127.0.0.1:8765`. The local CLI creates `.devguard/session-token` with private permissions if no environment token is supplied. It prints the path, never the token. No clipboard capture is enabled by startup.

Implemented foundation routes:

- `GET /health` and `GET /api/v1/health`: service readiness and whether the exact selected tag is installed.
- `GET /api/v1/status`: authenticated runtime and incomplete-feature status.
- `GET /api/v1/coverage`: authenticated capability statuses; privacy/capture/repair remain UNIMPLEMENTED.

`service_ready: true` does not mean the model, guard or repair pipeline works. `model_ready` here establishes installed-tag presence only; the smoke test establishes an inference/tool roundtrip separately.

Do not send private material to this foundation expecting protection. Guard and delivery routes are not implemented yet. The Ollama client is internal-only and accepts loopback HTTP endpoints, disables environment proxies and follows no redirects. The CLI currently provides only an operator token; scoped client-adapter credentials are future implementation work, so no adapter is claimed supported.

## After the model download finishes

```sh
.venv/bin/python -m devguard.models.smoke
```

This sends a synthetic arithmetic request to the real selected model, validates the model's native tool call, executes a bounded multiplication function and checks that the returned answer uses the real result. It reports only the result, timing and runtime metadata, never hidden reasoning.

Exit 0 is a successful tool roundtrip; exit 2 means the server or selected model is unavailable (the output distinguishes them); exit 1 means the real trial failed. This is not a privacy benchmark or backend repair proof. Do not label mock/unit tests as real inference success.

## Next implementation milestone

Mac 1 adds guard schemas, policy, validated redaction and the supported delivery gate, followed by the required optimised clipboard capture. Mac 2 owns repair/client adapters independently. Windows tasks can proceed against the shared contract with labelled fixtures.

The application does not use screenshots or recordings as diagnostic evidence. Clipboard text capture remains required but is currently disabled/unimplemented.
