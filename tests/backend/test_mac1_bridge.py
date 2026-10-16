"""Contract tests for the published Mac 1 async client shape; no real inference."""

import asyncio
import threading

import pytest

from devguard.agent.mac1_bridge import Mac1ModelBridge
from devguard.repair.contracts import SELECTED_MODEL, RepairError

RUNTIME = {
    "model_ready": True,
    "model": SELECTED_MODEL,
    "model_digest": "synthetic-unit-test-digest",
}


@pytest.fixture
def loop():
    event_loop = asyncio.new_event_loop()
    started = threading.Event()

    def run():
        event_loop.call_soon(started.set)
        event_loop.run_forever()

    thread = threading.Thread(target=run)
    thread.start()
    started.wait(timeout=2)
    yield event_loop
    event_loop.call_soon_threadsafe(event_loop.stop)
    thread.join(timeout=2)
    event_loop.close()


class FakeAsyncMac1Client:
    def __init__(self, *, runtime=None, response=None):
        self.runtime = runtime or RUNTIME
        self.response = response or {
            "message": {
                "tool_calls": [
                    {"function": {"name": "list_allowed_files", "arguments": {}}}
                ]
            }
        }
        self.calls = 0

    async def inspect(self):
        return self.runtime

    async def chat(self, messages, *, tools=None):
        self.calls += 1
        return self.response


def test_bridge_normalizes_actual_native_tool_shape(loop):
    client = FakeAsyncMac1Client()
    bridge = Mac1ModelBridge(client, loop, RUNTIME)
    assert bridge.next_action([], []) == {"tool": "list_allowed_files", "arguments": {}}
    assert client.calls == 1
    assert bridge.metadata["name"] == SELECTED_MODEL


def test_bridge_does_not_accept_model_digest_change(loop):
    client = FakeAsyncMac1Client(runtime={**RUNTIME, "model_digest": "changed"})
    bridge = Mac1ModelBridge(client, loop, RUNTIME)
    with pytest.raises(RepairError, match="MODEL_CHANGED"):
        bridge.next_action([], [])
    assert client.calls == 0


@pytest.mark.parametrize(
    "response",
    [
        {"message": {"content": "a prewritten answer"}},
        {"done_reason": "length", "message": {"tool_calls": []}},
        {
            "message": {
                "tool_calls": [{"function": {"name": "x", "arguments": "not-a-dict"}}]
            }
        },
        {"message": {"tool_calls": [{"function": {}}, {"function": {}}]}},
    ],
)
def test_bridge_requires_one_complete_native_action(loop, response):
    bridge = Mac1ModelBridge(FakeAsyncMac1Client(response=response), loop, RUNTIME)
    with pytest.raises(RepairError, match="INVALID_MODEL_ACTION"):
        bridge.next_action([], [])


def test_bridge_refuses_uninstalled_model(loop):
    with pytest.raises(RepairError, match="MODEL_NOT_PINNED"):
        Mac1ModelBridge(FakeAsyncMac1Client(), loop, {**RUNTIME, "model_ready": False})
