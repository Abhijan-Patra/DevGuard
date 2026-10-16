"""Context-schema validation only; injected outputs are not Gemma benchmarks."""

import asyncio
import json
import pytest

from devguard.guard.context import ContextInspector


class ModelDouble:
    def __init__(self, content):
        self.content, self.calls = content, 0
    async def chat(self, messages, **kwargs):
        self.calls += 1
        return {"message": {"content": self.content}}


@pytest.mark.parametrize("payload, task", [
    ({"decision": "ALLOW", "spans": [{"start": 0, "end": 1, "category": "CONFIDENTIAL"}]}, "debug"),
    ({"decision": "SANITIZE", "spans": []}, "debug"),
    ({"decision": "ALLOW", "spans": [], "private_reason": "not permitted"}, "debug"),
    ({"decision": "SANITIZE", "spans": [{"start": 0, "end": 1, "category": "IRRELEVANT"}]}, None),
])
def test_contradictory_or_unsafe_model_shapes_are_held(payload, task):
    async def run():
        inspector = ContextInspector(ModelDouble(json.dumps(payload)))
        assert await inspector.inspect("some input", task) is None
    asyncio.run(run())


def test_oversize_context_never_silently_truncates_into_a_model_call():
    async def run():
        model = ModelDouble('{"decision":"ALLOW","spans":[]}')
        inspector = ContextInspector(model)
        assert await inspector.inspect("x" * 2049, "debug") is None
        assert await inspector.inspect("\0" * 400, "debug") is None
        assert model.calls == 0
    asyncio.run(run())
