"""Contract tests for the published Mac 1 async client shape; no real inference."""

import pytest

from devguard.agent.mac1_bridge import DeferredMac1ModelBridge, Mac1ModelBridge
from devguard.repair.contracts import SELECTED_MODEL, RepairError

RUNTIME = {
    "model_ready": True,
    "model": SELECTED_MODEL,
    "model_digest": "synthetic-unit-test-digest",
}


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


def test_deferred_bridge_does_not_query_missing_model_during_startup(loop):
    client = FakeAsyncMac1Client(runtime={**RUNTIME, "model_ready": False})
    bridge = DeferredMac1ModelBridge(client, loop)
    assert bridge._bridge is None
    assert client.calls == 0
    with pytest.raises(RepairError, match="MODEL_NOT_PINNED"):
        _ = bridge.metadata


def test_deferred_bridge_pins_actual_runtime_on_first_worker_call(loop):
    bridge = DeferredMac1ModelBridge(FakeAsyncMac1Client(), loop)
    assert bridge.next_action([], []) == {"tool": "list_allowed_files", "arguments": {}}
    assert bridge.metadata["digest"] == RUNTIME["model_digest"]
