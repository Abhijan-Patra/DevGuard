"""Declared doubles verify client authority, never Gemma accuracy or native coverage."""
import asyncio
import json
import os

from fastapi.testclient import TestClient
import httpx
import pytest

from devguard.client import GuardedClient, private_token
from devguard.schemas.guard import Category, Decision, ModelProposal, Span
from tests.integration.test_professional_workspace import app_for, AUTH
from tests.guard.test_guard import TestInspector, TestScanner, request
from devguard.guard.engine import GuardEngine, GuardError
from devguard.storage.audit import AuditStore
from integrations.codex import hook


def test_registered_source_client_releases_once_and_never_returns_raw_credential(tmp_path):
    app,spec,_=app_for(tmp_path)
    (spec.root/'cart.py').write_text('password="synthetic-private-credential-091345"\nVALUE=42\n')
    with TestClient(app) as c:
        body={'project_id':'demo','path':'cart.py','content_version':1}
        result=c.post('/api/v1/client/context',json=body,headers=AUTH).json()
        assert result['delivered'] and result['decision']=='SANITIZE'
        assert 'synthetic-private' not in json.dumps(result)
        assert 'VALUE=42' in result['text'] and result['safe_preview'] is None
        assert app.state.guard.records[result['request_id']].candidate is None
        assert c.post('/api/v1/guard/requests/'+result['request_id']+'/deliver',headers=AUTH,
                      json={'content_version':1,'destination_id':'managed-client'}).status_code==409
        assert 'synthetic-private' not in json.dumps(c.get('/api/v1/events',headers=AUTH).json())


@pytest.mark.parametrize('path',['../private.py','.env','/etc/passwd','not-registered.py'])
def test_client_context_denies_non_manifest_paths(tmp_path,path):
    app,_,_=app_for(tmp_path)
    with TestClient(app) as c:
        assert c.post('/api/v1/client/context',headers=AUTH,
                      json={'project_id':'demo','path':path,'content_version':1}).status_code==403
        assert c.get('/api/v1/client/sources').status_code==401


def test_client_final_source_check_refuses_mutation_during_inspection(tmp_path):
    app,spec,_=app_for(tmp_path)
    class EditingInspector:
        async def inspect(self,text,task):
            (spec.root/'cart.py').write_text('VALUE=999\n')
            return ModelProposal(decision=Decision.ALLOW,spans=[])
    app.state.guard.inspector=EditingInspector()
    with TestClient(app) as c:
        r=c.post('/api/v1/client/context',headers=AUTH,json={'project_id':'demo','path':'cart.py','content_version':1})
        assert r.status_code==409 and r.json()['error']['code']=='STALE_SOURCE'
        assert 'VALUE' not in r.text


def test_client_no_bytes_for_confidential_or_injection_proposal(tmp_path):
    app,_,_=app_for(tmp_path)
    app.state.guard.inspector=TestInspector(ModelProposal(decision=Decision.SANITIZE,
        spans=[Span(start=0,end=5,category=Category.CONFIDENTIAL)]))
    with TestClient(app) as c:
        result=c.post('/api/v1/client/context',headers=AUTH,json={'project_id':'demo','path':'cart.py','content_version':1}).json()
        assert result['decision']=='REVIEW' and result['text'] is None


def test_managed_tool_hook_opt_in_only_never_allows_native_shell():
    never=lambda *args:pytest.fail('No classifier should grant tool authority')
    for name in ('mcp__devguard__list_sources','mcp__devguard__read_source'):
        event={'hook_event_name':'PreToolUse','tool_name':name}
        assert hook.handle(event,never,managed_tools=True)=={}
        assert hook.handle(event,never)['hookSpecificOutput']['permissionDecision']=='deny'
    for name in ('Bash','Read','mcp__other__read_source','mcp__devguard__apply','exec_command'):
        assert hook.handle({'hook_event_name':'PreToolUse','tool_name':name},never,managed_tools=True)['hookSpecificOutput']['permissionDecision']=='deny'


def test_stdio_client_holds_failures_and_cannot_select_remote_guard():
    with pytest.raises(ValueError):GuardedClient('https://evil.invalid/api/v1','test')
    async def scenario():
        sent=[]
        def response(r):
            sent.append(r)
            return httpx.Response(503,json={'error':'unavailable'})
        c=GuardedClient('http://127.0.0.1:8765/api/v1','synthetic',transport=httpx.MockTransport(response))
        assert (await c.read('demo','../outside'))['text'] is None
        assert not sent
        assert (await c.read('demo','cart.py'))['status']=='HELD'
        assert len(sent)==1 and sent[0].url.path=='/api/v1/client/context'
        await c.api.aclose()
    asyncio.run(scenario())


def test_private_client_token_refuses_symlink_public_mode_or_multiple_links(tmp_path):
    path=tmp_path/'token';path.write_text('synthetic-local-client-token-not-real-0123456789');path.chmod(0o600)
    assert private_token(path).startswith('synthetic')
    link=tmp_path/'link';link.symlink_to(path)
    with pytest.raises(OSError):private_token(link)
    path.chmod(0o644)
    with pytest.raises(ValueError):private_token(path)
    path.chmod(0o600);os.link(path,tmp_path/'hardlink')
    with pytest.raises(ValueError):private_token(path)


def test_scoped_client_can_read_but_has_no_operator_authority(tmp_path):
    token='synthetic-restricted-client-token-924017563890'
    app,_,_=app_for(tmp_path,adapter_token=token)
    headers={'Authorization':'Bearer '+token}
    with TestClient(app) as c:
        assert c.get('/api/v1/client/sources',headers=headers).status_code==200
        result=c.post('/api/v1/client/context',headers=headers,json={'project_id':'demo','path':'cart.py','content_version':1}).json()
        assert result['text']=='VALUE = 1\n' and result['delivered']
        assert c.get('/api/v1/status',headers=headers).status_code==401
        assert c.get('/api/v1/composer',headers=headers).status_code==401
        assert c.post('/api/v1/scheduler/enter-idle',headers=headers,json={}).status_code==401
        assert c.post('/api/v1/clipboard/enable',headers=headers,json={'consent':True}).status_code==401


def test_client_profile_is_isolated_and_never_embeds_token_or_grants_native_shell(tmp_path):
    from devguard.client_config import prepare
    token=tmp_path/'client-token';token.write_text('synthetic-only-client-token-7865041298');token.chmod(0o600)
    profile=tmp_path/'profile'
    result=prepare(profile,token,'http://127.0.0.1:8765/api/v1')
    assert not result['hooks_trusted'] and not result['global_configuration_changed']
    content='\n'.join(p.read_text() for p in profile.rglob('*') if p.is_file())
    assert token.read_text() not in content and 'dangerously-bypass' not in content
    assert 'read-only' in content and 'web_search = "disabled"' in content
    assert 'enabled_tools = ["list_sources", "read_source"]' in content
    with pytest.raises(FileExistsError):prepare(profile,token,'http://127.0.0.1:8765/api/v1')
