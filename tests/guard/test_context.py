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


def test_exact_quotes_compute_unicode_spans_without_model_offsets():
    async def run():
        model = ModelDouble(json.dumps({'decision':'SANITIZE','redactions':[
            {'text':'Alice','category':'PERSONAL_DATA'}]}))
        proposal = await ContextInspector(model).inspect('🙂Alice error','debug')
        assert proposal.spans[0].start == 1 and proposal.spans[0].end == 6
    asyncio.run(run())


@pytest.mark.parametrize('text,quoted',[('Alice Alice','Alice'),('Alice','invented'),
                                      ('Alice','')])
def test_missing_ambiguous_and_empty_quotes_hold(text,quoted):
    async def run():
        model=ModelDouble(json.dumps({'decision':'SANITIZE','redactions':[
            {'text':quoted,'category':'PERSONAL_DATA'}]}))
        assert await ContextInspector(model).inspect(text,'debug') is None
    asyncio.run(run())


@pytest.mark.parametrize("payload, task", [
    ({"decision": "ALLOW", "redactions": [{"text": "some", "category": "CONFIDENTIAL"}]}, "debug"),
    ({"decision": "SANITIZE", "redactions": []}, "debug"),
    ({"decision": "ALLOW", "redactions": [], "private_reason": "not permitted"}, "debug"),
    ({"decision": "SANITIZE", "redactions": [{"text": "some", "category": "IRRELEVANT"}]}, None),
    ({"decision": "SANITIZE", "redactions": [{"text": "some input", "category": "CONFIDENTIAL"},
        {"text": "input", "category": "PERSONAL_DATA"}]}, "debug"),
])
def test_contradictory_or_unsafe_model_shapes_are_held(payload, task):
    async def run():
        inspector = ContextInspector(ModelDouble(json.dumps(payload)))
        assert await inspector.inspect("some input", task) is None
    asyncio.run(run())


def test_oversize_context_never_silently_truncates_into_a_model_call():
    async def run():
        model = ModelDouble('{"decision":"ALLOW","redactions":[]}')
        inspector = ContextInspector(model)
        assert await inspector.inspect("x" * 2049, "debug") is None
        assert await inspector.inspect("\0" * 400, "debug") is None
        assert model.calls == 0
    asyncio.run(run())
