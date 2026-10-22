"""Tool authority/history regressions with declared fake ports, not model accuracy."""

import json

import pytest

from devguard.agent.tool_messages import append_tool_exchange
from devguard.repair.contracts import RepairError
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


def test_one_native_transport_format_failure_can_recover_without_executing_it(
    spec, tmp_path
):
    class RecoveringModel(FakeModel):
        failed = False

        def next_action(self, messages, tools):
            if not self.failed:
                self.failed = True
                raise RepairError("INVALID_MODEL_ACTION")
            return super().next_action(messages, tools)

    model = RecoveringModel(*fake_actions())
    service, _ = service_for(spec, tmp_path, model=model)
    result = run_once(service)
    assert result.state == "READY_FOR_REVIEW"
    assert len(result.completed_tools) == 2
    assert "exactly ONE" in model.messages[0][-1]["content"]


def test_repeated_native_transport_format_failure_stops_without_fake_actions(
    spec, tmp_path
):
    class BrokenFormat(FakeModel):
        attempts = 0

        def next_action(self, messages, tools):
            self.attempts += 1
            raise RepairError("INVALID_MODEL_ACTION")

    model = BrokenFormat()
    service, _ = service_for(spec, tmp_path, model=model)
    result = run_once(service)
    assert (result.state, result.reason_code) == ("BLOCKED", "INVALID_MODEL_ACTION")
    assert model.attempts == 2
    assert result.completed_tools == []


def test_generated_syntax_error_is_feedback_within_existing_patch_budget(spec, tmp_path):
    from devguard.repair.contracts import TestResult as CheckResult
    from devguard.repair.workspace import digest
    invalid = '```python\nVALUE = 2\n```\n'
    model = FakeModel(
        {'tool':'read_allowed_file','arguments':{'path':'cart.py'}},
        {'tool':'propose_patch','arguments':{'path':'cart.py','expected_hash':digest(b'VALUE = 1\n'),'content':invalid}},
        {'tool':'run_named_test','arguments':{'name':'cart'}},
        {'tool':'propose_patch','arguments':{'path':'cart.py','expected_hash':digest(invalid.encode()),'content':'VALUE = 2\n'}},
        {'tool':'run_named_test','arguments':{'name':'cart'}},
        {'tool':'finish','arguments':{}},
    )
    class Checks:
        outcomes=iter([CheckResult('FAIL','declared baseline',1),
            CheckResult('ERROR','declared source SyntaxError',2),
            CheckResult('PASS','declared revised check',0),CheckResult('PASS','declared final independent check',0)])
        def run(self,*args):return next(self.outcomes)
    service,_=service_for(spec,tmp_path,model=model,verifier=Checks())
    run=run_once(service)
    assert run.state == 'READY_FOR_REVIEW'
    feedback=json.loads(model.messages[3][-1]['content'])
    assert feedback['status']=='ERROR' and feedback['reason_code']=='SOURCE_SYNTAX_ERROR'
    assert feedback['source_errors']==[{'path':'cart.py','line':1}]
    assert (spec.root/'cart.py').read_bytes()==b'VALUE = 1\n'


def test_checker_error_with_valid_source_still_holds_after_patch(spec,tmp_path):
    from devguard.repair.contracts import TestResult as CheckResult
    model=FakeModel(*fake_actions()[:2], {'tool':'run_named_test','arguments':{'name':'cart'}})
    class Checks:
        outcomes=iter([CheckResult('FAIL','declared baseline',1),CheckResult('ERROR','declared checker error',2)])
        def run(self,*args):return next(self.outcomes)
    service,_=service_for(spec,tmp_path,model=model,verifier=Checks())
    run=run_once(service)
    assert (run.state,run.reason_code)==('BLOCKED','CHECK_UNAVAILABLE')
    assert not service.patches.candidates
    assert (spec.root/'cart.py').read_bytes()==b'VALUE = 1\n'


def test_model_checksum_is_not_source_version_authority(spec,tmp_path):
    actions=fake_actions()
    actions[1]['arguments']['expected_hash']='b'*64
    model=FakeModel(*actions)
    service,_=service_for(spec,tmp_path,model=model)
    run=run_once(service)
    assert run.state=='READY_FOR_REVIEW'
    assert (spec.root/'cart.py').read_bytes()==b'VALUE = 1\n'
    patch_tool=next(t for t in __import__('devguard.agent.repair_agent',fromlist=['TOOLS']).TOOLS if t['function']['name']=='propose_patch')
    assert 'expected_hash' not in patch_tool['function']['parameters']['properties']


def test_trusted_read_binding_refuses_changed_sandbox_even_if_model_hash_matches(spec,tmp_path):
    from threading import Event
    from devguard.agent.repair_agent import investigate
    from devguard.repair.workspace import capture,digest
    snapshot=capture(spec,tmp_path/'private-snapshot')
    changed=b'CONCURRENT = 1\n'
    class ConcurrentModel(FakeModel):
        calls=0
        def next_action(self,messages,tools):
            self.calls+=1
            if self.calls==2:(snapshot.source/'cart.py').write_bytes(changed)
            return super().next_action(messages,tools)
    model=ConcurrentModel({'tool':'read_allowed_file','arguments':{'path':'cart.py'}},
        {'tool':'propose_patch','arguments':{'path':'cart.py','expected_hash':digest(changed),'content':'VALUE = 2\n'}})
    try:
        with pytest.raises(RepairError,match='STALE_SANDBOX'):
            investigate(model=model,guard=FakeGuard(),verifier=FakeVerifier(),spec=spec,
                snapshot=snapshot,test_name='cart',baseline_output='declared synthetic failure',
                cancel=Event(),on_tool=lambda name:None)
        assert (snapshot.source/'cart.py').read_bytes()==changed
        assert (spec.root/'cart.py').read_bytes()==b'VALUE = 1\n'
    finally:snapshot.close()
