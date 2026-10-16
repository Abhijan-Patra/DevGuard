"""Tool authority/history regressions with declared fake ports, not model accuracy."""

import json

import pytest

from devguard.agent.tool_messages import append_tool_exchange
from tests.backend.test_repair import (
    FakeGuard,
    FakeModel,
    FakeVerifier,
    fake_actions,
    run_once,
    service_for,
)


def test_tool_history_uses_native_calls_and_guarded_tool_roles(spec, tmp_path):
    model = FakeModel(*fake_actions())
    service, _ = service_for(spec, tmp_path, model=model)
    run = run_once(service)
    assert run.state == "READY_FOR_REVIEW"
    call, result = model.messages[1][-2:]
    assert call == {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "function": {
                    "name": "read_allowed_file",
                    "arguments": {"path": "cart.py"},
                }
            }
        ],
    }
    assert result["role"] == "tool"
    assert result["tool_name"] == "read_allowed_file"
    assert json.loads(result["content"])["content"] == "VALUE = 1\n"
    patch_call, patch_result = model.messages[2][-2:]
    assert patch_call["tool_calls"][0]["function"]["name"] == "propose_patch"
    assert json.loads(patch_result["content"])["originals_modified"] is False


def test_raw_tool_result_never_replaces_guard_approved_history(spec, tmp_path):
    class RedactingGuard(FakeGuard):
        def sanitize(self, text, *, purpose):
            self.calls.append(purpose)
            return (
                '{"content":"declared-cleaned-result"}'
                if purpose == "tool_result"
                else text
            )

    model = FakeModel(
        {"tool": "read_allowed_file", "arguments": {"path": "cart.py"}},
        {"tool": "finish", "arguments": {}},
    )
    service, _ = service_for(spec, tmp_path, model=model, guard=RedactingGuard())
    assert run_once(service).state == "UNRESOLVED"
    history = model.messages[1]
    assert "VALUE = 1" not in json.dumps(history)
    assert json.loads(history[-1]["content"]) == {"content": "declared-cleaned-result"}


def test_model_cannot_invoke_an_unregistered_check_even_through_a_custom_port(
    spec, tmp_path
):
    model = FakeModel({"tool": "run_named_test", "arguments": {"name": "not_enrolled"}})
    verifier = FakeVerifier("FAIL")
    service, _ = service_for(spec, tmp_path, model=model, verifier=verifier)
    run = run_once(service)
    assert (run.state, run.reason_code) == ("BLOCKED", "TEST_DENIED")
    assert verifier.calls == 1  # Only the trusted baseline reached the verifier.


@pytest.mark.parametrize("status", ["ERROR", "TIMEOUT", "CANCELED"])
def test_unavailable_check_does_not_continue_into_a_patch(spec, tmp_path, status):
    model = FakeModel({"tool": "run_named_test", "arguments": {"name": "cart"}})
    service, _ = service_for(
        spec, tmp_path, model=model, verifier=FakeVerifier("FAIL", status)
    )
    run = run_once(service)
    expected = (
        ("CANCELED", "CANCELED")
        if status == "CANCELED"
        else ("BLOCKED", "CHECK_UNAVAILABLE")
    )
    assert (run.state, run.reason_code) == expected
    assert run.candidate_id is None
    assert len(model.messages) == 1


def test_patch_requires_an_approved_read_of_the_target(spec, tmp_path):
    model = FakeModel(fake_actions()[1])
    service, _ = service_for(spec, tmp_path, model=model)
    run = run_once(service)
    assert (run.state, run.reason_code) == ("BLOCKED", "READ_BEFORE_PATCH_REQUIRED")
    assert (spec.root / "cart.py").read_text() == "VALUE = 1\n"
    assert not service.patches.candidates


def test_cancel_during_guard_does_not_deliver_result_or_call_model_again(
    spec, tmp_path
):
    class CancelingGuard(FakeGuard):
        cancel = None

        def sanitize(self, text, *, purpose):
            if purpose == "tool_result":
                self.cancel.set()
            return text

    guard = CancelingGuard()
    model = FakeModel(*fake_actions())
    service, _ = service_for(spec, tmp_path, model=model, guard=guard)
    incident = service.create_incident("demo", "cart")
    run = service.queue(incident["incident_id"])
    guard.cancel = run.cancel
    service.execute(run.run_id)
    assert run.state == "CANCELED"
    assert run.completed_tools == []
    assert len(model.messages) == 1
    assert (spec.root / "cart.py").read_text() == "VALUE = 1\n"


def test_tool_history_copies_nested_arguments_without_model_prose():
    arguments = {"nested": {"value": "declared synthetic argument"}}
    messages = []
    append_tool_exchange(messages, name="probe", arguments=arguments, result="approved")
    arguments["nested"]["value"] = "changed later"
    assert (
        messages[0]["tool_calls"][0]["function"]["arguments"]["nested"]["value"]
        == "declared synthetic argument"
    )
    assert messages[0]["content"] == ""
    assert "thinking" not in messages[0]
