"""Trusted startup configuration; model access stays on loopback."""

from dataclasses import dataclass, field
import os
from urllib.parse import urlsplit

MODEL = "gemma4:e4b-it-q4_K_M"


@dataclass(frozen=True)
class Settings:
    session_token: str = field(repr=False)
    ollama_url: str = "http://127.0.0.1:11434"
    model: str = MODEL

    def __post_init__(self):
        if len(self.session_token) < 32:
            raise ValueError("Use a session token of at least 32 characters")
        url = urlsplit(self.ollama_url)
        if (
            url.scheme != "http"
            or url.hostname not in {"127.0.0.1", "localhost", "::1"}
            or url.username or url.password or url.query or url.fragment
            or url.path not in {"", "/"}
        ):
            raise ValueError("Only a loopback Ollama HTTP endpoint is supported")
        if self.model != MODEL:
            raise ValueError("This implementation pins the selected Gemma E4B Q4 tag")

    @classmethod
    def from_environment(cls, token: str):
        return cls(
            session_token=token,
            ollama_url=os.environ.get("DEVGUARD_OLLAMA_URL", "http://127.0.0.1:11434"),
            model=os.environ.get("DEVGUARD_MODEL", MODEL),
        )
