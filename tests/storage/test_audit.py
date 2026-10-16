"""Real SQLite persistence and concurrent worker/API metadata boundaries."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import os

import pytest

from devguard.guard.engine import GuardEngine
from devguard.schemas.guard import Decision, GuardInput, ModelProposal
from devguard.storage.audit import AuditStore, AuditUnavailable
from tests.guard.test_guard import TestInspector, TestScanner


def repair_event():
    return {'kind': 'run.state', 'state': 'BLOCKED', 'run_id': 'run-'+'a'*32,
            'project_id': 'demo-cart', 'redacted_summary': 'SYNTHETIC_PRIVATE_NEVER_STORE',
            'raw_payload': 'SYNTHETIC_PRIVATE_NEVER_STORE', 'evidence_refs': ['private']}


def test_persistence_and_redacted_repair_sink(tmp_path):
    path=tmp_path/'private'/'audit.sqlite3'
    store=AuditStore(path)
    assert store.durable
    store.add('guard.decision','REVIEW',reason_codes=['MODEL_UNAVAILABLE','PRIVATE_UNKNOWN_REASON'])
    store.add_repair(repair_event())
    cursor=store.events()['next_cursor']
    store.close()
    reopened=AuditStore(path)
    events=reopened.events()
    assert events['next_cursor']==cursor and len(events['events'])==2
    assert 'SYNTHETIC_PRIVATE' not in json.dumps(events)
    assert 'PRIVATE_UNKNOWN' not in json.dumps(events)
    assert events['events'][1]['run_id']=='run-'+'a'*32
    assert path.stat().st_mode & 0o077 == 0
    reopened.close()


def test_concurrent_writes_and_reads_are_serialized(tmp_path):
    store=AuditStore(tmp_path/'private'/'audit.sqlite3')
    def write(_):
        store.add_repair(repair_event())
        store.events()
    with ThreadPoolExecutor(max_workers=8) as workers:
        list(workers.map(write,range(60)))
    result=store.events()
    assert len(result['events'])==60 and result['next_cursor']=='60'
    store.close()


def test_nonprivate_symlink_and_hardlink_storage_are_rejected(tmp_path):
    public=tmp_path/'public'
    public.mkdir(mode=0o755)
    with pytest.raises(AuditUnavailable):
        AuditStore(public/'audit.sqlite3')
    private=tmp_path/'private'
    private.mkdir(mode=0o700)
    target=private/'target'
    target.touch(mode=0o600)
    (private/'linked').symlink_to(target)
    with pytest.raises(AuditUnavailable):
        AuditStore(private/'linked')
    os.link(target,private/'hardlinked')
    with pytest.raises(AuditUnavailable):
        AuditStore(private/'hardlinked')


def test_store_failure_revokes_guard_candidate_and_exposes_only_fixed_error():
    async def run():
        audit=AuditStore()
        audit.close()
        guard=GuardEngine(TestScanner(),TestInspector(ModelProposal(decision=Decision.ALLOW,spans=[])),audit)
        with pytest.raises(AuditUnavailable,match='^AUDIT_UNAVAILABLE$'):
            await guard.evaluate(GuardInput(text='synthetic benign evidence',surface='tool_result',
                                           destination_id='local-preview',content_version=1))
        assert not guard.records
    asyncio.run(run())
