"""Cross-platform security cases: Windows syntax must not expand source scope."""
import pytest
from devguard.windows import relative_parts
from devguard.repair.workspace import safe_relative
from devguard.repair.contracts import RepairError


@pytest.mark.parametrize('name', ['C:/secret', 'C:secret', '//host/share', 'a:stream',
    'a/../b', 'CON', 'con.txt', 'dir/NUL.py', 'COM1.log', 'a.', 'a ', 'a\\b',
    'x//y', './a', 'x\0y', 'a?/b', 'x\x01y', 'COM¹.txt', 'LPT²', 'CON .txt'])
def test_windows_aliases_devices_streams_and_traversal_are_rejected(name):
    with pytest.raises(OSError):relative_parts(name)
    with pytest.raises(RepairError):safe_relative(name)


def test_unicode_and_nested_normal_paths_remain_usable():
    assert relative_parts('src/café.py') == ['src', 'café.py']
    assert safe_relative('src/café.py') == 'src/café.py'


@pytest.mark.parametrize('args,expected', [
    (['ollama.exe','pull','gemma4:e4b-it-q4_K_M'], True),
    (['ollama.exe','pull','another-tag'], False),
    (None, 'HELD'),
])
def test_exact_model_pull_check_never_assumes_unreadable_ollama_is_idle(monkeypatch, args, expected):
    import sys
    from types import SimpleNamespace
    from devguard.windows import exact_pull_active
    class ProcessError(Exception):pass
    fake = SimpleNamespace(Error=ProcessError, process_iter=lambda attributes: iter([
        SimpleNamespace(info={'name':'ollama.exe','cmdline':args})]))
    monkeypatch.setitem(sys.modules, 'psutil', fake)
    if expected == 'HELD':
        with pytest.raises(RuntimeError):exact_pull_active('gemma4:e4b-it-q4_K_M')
    else:
        assert exact_pull_active('gemma4:e4b-it-q4_K_M') is expected
