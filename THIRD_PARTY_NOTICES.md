# Sources and third-party notices

Original repository material is under MIT. External model weights, tools and dependencies are not relicensed by that file. No model weights or third-party source are bundled in this documentation package. Before distributing a runtime/image, preserve the actual selected packages' licence/NOTICE requirements.

## Model

Gemma 4 is developed by Google DeepMind. Its official model card lists Apache License 2.0 and documents coding/function-calling capabilities. This is an open-weight model selection; no claim is made that the repository reproduces its training pipeline/data.

- [Official Gemma 4 model card](https://ai.google.dev/gemma/docs/core/model_card_4)
- [Selected Ollama Gemma 4 E4B package](https://ollama.com/library/gemma4:e4b)
- [Ollama context/runtime FAQ](https://docs.ollama.com/faq)
- [Hosted Gemma API guide, alternative deployment only](https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api)

## Client integrations

- [Official OpenAI documentation: hooks](https://developers.openai.com/codex/hooks)
- [Claude Code hooks](https://code.claude.com/docs/en/hooks)

Installed-client behaviour and complete context-path coverage remain to be tested. Antigravity is used for development by two teammates; no protected-runtime integration is claimed.

## Implementation references

- [Gitleaks](https://github.com/gitleaks/gitleaks)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Pydantic](https://docs.pydantic.dev/latest/)
- [Streamlit](https://docs.streamlit.io/)
- [pytest](https://docs.pytest.org/en/stable/)
- [HTTPX](https://www.python-httpx.org/)
- [Ruff](https://docs.astral.sh/ruff/)
- [watchdog](https://github.com/gorakhargosh/watchdog)
- [psutil](https://github.com/giampaolo/psutil)
- [Docker security](https://docs.docker.com/engine/security/)
- [Apple NSPasteboard](https://developer.apple.com/documentation/appkit/nspasteboard)
- [Git ignore behaviour](https://git-scm.com/docs/gitignore)

## Cloud reference

- [DigitalOcean CPU pricing](https://www.digitalocean.com/pricing/droplets)
- [DigitalOcean GPU pricing](https://www.digitalocean.com/pricing/gpu-droplets)
- [Droplet billing](https://docs.digitalocean.com/products/droplets/details/pricing/)
- [Signup credit](https://docs.digitalocean.com/platform/billing/signup-credit/)

Model, client-hook and price pages were checked on 16 October 2026. Architecture, budgets, polling intervals, limits, ownership and milestones are project recommendations, not measured results or official scoring criteria. Track descriptions, deadline and team size come from the user's supplied event guideline/screenshots; confirm submission eligibility and multiple-category rules with the organiser.
