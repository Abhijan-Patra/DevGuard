# Contributing

Read the [architecture](docs/ARCHITECTURE.md), [API contract](docs/API_CONTRACT.md), [privacy/execution policy](docs/SECURITY_POLICY.md) and [repository instructions](AGENTS.md). Historical team task files describe original ownership; contributors do not need those machines or accounts.

Use a separate branch, small reviewable pull requests and synthetic reproduction data. Explain the problem, resulting behavior, actual verification and limitations. Coordinate changes to shared schemas, dependency pins, model policy and trusted test boundaries in the pull request.

## Development checks

With Python 3.11 or 3.12:

```sh
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.lock.txt -r requirements-ui.lock.txt -r requirements-client.lock.txt
python -m pip install --no-deps -e .
python -m pytest -q
python -m pip check
node --check devguard/web/workspace.js
```

Node.js is a development syntax-check dependency, not an application runtime dependency. The full suite uses declared doubles and local HTTP test servers; it does not prove unseen model accuracy or physical-device clipboard behavior. Native/model/Docker trials must be sequential and explicitly scoped. Never enable the real system clipboard for an automated test; use a private named pasteboard and synthetic text.

The packaged public demo/oracle copies under `devguard/resources/` must match their reviewed originals; a test enforces consistency. Keep the Docker build context to the two public inputs. Do not weaken the independent oracle to accommodate a model answer.

Use one runtime model, `gemma4:e4b-it-q4_K_M`, with its pinned digest. Runtime models cannot change policy, source enrollment, test commands or apply authority. Clipboard capture remains required, opt-in and text-only. Backend investigation uses source, structured logs, diffs, named probes and independent tests; screenshots/recordings/keyboard monitoring are excluded.

Do not submit private inputs, credentials, clipboard history, model weights, databases, runtime logs or snapshots. Preserve dependency notices. See [release checklist](docs/RELEASE_CHECKLIST.md) before packaging or tagging a release.
