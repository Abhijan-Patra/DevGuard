"""Readiness and local-authority checks; these do not mock a successful model trial."""

import asyncio

from fastapi.testclient import TestClient
import httpx
import pytest

from devguard.api.app import create_app
from devguard.config import MODEL, Settings
from devguard.models.ollama import ModelUnavailable, OllamaClient

TOKEN = "unit-test-token-not-valid-in-production-000"


def transport(request):
    if request.url.path == "/api/version":
        return httpx.Response(200, json={"version": "test-version"})
    return httpx.Response(200, json={"models": []})


def test_auth_and_missing_model_are_not_reported_as_ready():
    with TestClient(create_app(Settings(TOKEN), transport=httpx.MockTransport(transport))) as api:
        assert api.get("/health").json() == {"service_ready": True, "model_ready": False}
        assert api.get("/api/v1/status").status_code == 401
        assert api.get("/api/v1/status", headers={"Authorization": "Bearer wrong"}).status_code == 401
        result = api.get("/api/v1/status", headers={"Authorization": f"Bearer {TOKEN}"}).json()
        assert result["runtime"]["model"] == MODEL
        assert result["runtime"]["model_digest"] is None
        assert result["clipboard"]["enabled"] is False
        assert result["guard_implemented"] is False


@pytest.mark.parametrize("url", [
    "https://example.invalid", "http://192.168.1.2:11434", "http://localhost@external.invalid",
    "http://127.0.0.1:11434/another-path", "http://127.0.0.1:11434?forward=external",
])
def test_runtime_rejects_nonlocal_destinations(url):
    with pytest.raises(ValueError):
        Settings(TOKEN, ollama_url=url)


def test_failed_runtime_does_not_echo_its_response_body():
    async def exercise():
        mock = httpx.MockTransport(lambda r: httpx.Response(500, text="PRIVATE_RESPONSE_SENTINEL"))
        client = OllamaClient(Settings(TOKEN), transport=mock)
        try:
            assert (await client.inspect())["model_ready"] is False
            with pytest.raises(ModelUnavailable) as error:
                await client.chat([{"role": "user", "content": "Synthetic input"}])
            assert "PRIVATE_RESPONSE_SENTINEL" not in str(error.value)
        finally:
            await client.close()
    asyncio.run(exercise())
