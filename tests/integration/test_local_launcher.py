"""Process ownership checks must survive macOS interpreter canonicalisation."""
from types import SimpleNamespace
import os
import pytest

pytestmark = pytest.mark.skipif(os.name == "nt", reason="POSIX ps identity; Windows process/event tests cover the native equivalent")
from devguard import local


def test_owned_compares_module_arguments_and_process_start_not_interpreter_alias(monkeypatch):
    def run(args,**kwargs):
        if args[-1]=='lstart=':return SimpleNamespace(stdout='Wed Oct 21 12:00:00 2026\n',returncode=0)
        return SimpleNamespace(stdout='/canonical/Python -m devguard --port 8765 --projects-config /local/reviewed.json\n',returncode=0)
    monkeypatch.setattr(local.subprocess,'run',run)
    record={'pid':123,'port':8765,'command':'/venv/bin/python -m devguard --port 8765 --projects-config /local/reviewed.json','process_start':'Wed Oct 21 12:00:00 2026'}
    assert local.owned(record)
    assert not local.owned({**record,'process_start':'different start time'})
    assert not local.owned({**record,'command':'/venv/bin/python -m devguard --port 8765 --projects-config /another/project.json'})
    assert not local.owned({**record,'port':9999})
    assert not local.owned({'pid':123,'port':8765})
