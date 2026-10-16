"""Bounded local Ollama calls. Never log prompt or response bodies."""

import asyncio
import httpx

from devguard.config import Settings
from devguard.models.queue import InferenceQueue, QueueUnavailable


class ModelUnavailable(Exception):
    """A fixed, non-sensitive runtime failure."""


class OllamaClient:
    def __init__(self, settings: Settings, transport=None):
        self.settings = settings
        self._client = httpx.AsyncClient(
            base_url=settings.ollama_url,
            timeout=httpx.Timeout(120, connect=5),
            follow_redirects=False,
            trust_env=False,
            transport=transport,
        )
        self.queue = InferenceQueue()

    async def close(self):
        await self.queue.close()
        await self._client.aclose()

    async def inspect(self):
        try:
            version, tags = await asyncio.gather(
                self._client.get("/api/version", timeout=5),
                self._client.get("/api/tags", timeout=5),
            )
            version.raise_for_status()
            tags.raise_for_status()
            selected = next(
                (m for m in tags.json().get("models", [])
                 if m.get("name") == self.settings.model), None
            )
            return {
                "server_ready": True,
                "server_version": version.json().get("version"),
                "model": self.settings.model,
                "model_ready": selected is not None,
                "model_digest": selected.get("digest") if selected else None,
            }
        except (httpx.HTTPError, ValueError, TypeError, AttributeError):
            return {
                "server_ready": False,
                "server_version": None,
                "model": self.settings.model,
                "model_ready": False,
                "model_digest": None,
            }

    async def chat(self, messages, *, tools=None, output_format=None, priority="background"):
        """Internal adapter only; callers must enforce their guard policy."""
        payload = {
            "model": self.settings.model,
            "messages": messages,
            "stream": False,
            "think": False,
            "keep_alive": "5m",
            "options": {"num_ctx": 4096, "num_predict": 512},
        }
        if tools:
            payload["tools"] = tools
        if output_format:
            payload["format"] = output_format
        try:
            async with self.queue.slot(priority):
                response = await self._client.post("/api/chat", json=payload)
                response.raise_for_status()
                result = response.json()
                if not isinstance(result.get("message"), dict):
                    raise ValueError("Missing model message")
                return result
        except (httpx.HTTPError, QueueUnavailable, ValueError, TypeError, AttributeError):
            raise ModelUnavailable("Local model call failed or returned invalid data") from None
