import pytest
import os

pytestmark = pytest.mark.skipif(os.name != "posix", reason="Descriptor-anchored project reads target the Mac backend")

from devguard.guard.engine import GuardError
from devguard.guard.paths import ProjectFiles


def test_approved_file_only_and_symlinks_never_escape(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "source.py").write_text("print('benign')\n")
    (project / ".env").write_text("synthetic only")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "private.txt").write_text("outside synthetic data")
    (project / "escaped.txt").symlink_to(outside / "private.txt")
    (project / "escaped-dir").symlink_to(outside, target_is_directory=True)
    files = ProjectFiles(project)
    try:
        assert files.read_text("source.py") == "print('benign')\n"
        for path in (".env", ".ENV", "../outside/private.txt", "/etc/passwd", "..\\outside", "escaped.txt", "escaped-dir/private.txt"):
            with pytest.raises(GuardError):
                files.read_text(path)
    finally:
        files.close()


def test_open_project_descriptor_does_not_follow_replacement_root(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    (root / "source.txt").write_text("original approved source")
    files = ProjectFiles(root)
    root.rename(tmp_path / "renamed")
    root.mkdir()
    (root / "source.txt").write_text("replacement directory")
    try:
        assert files.read_text("source.txt") == "original approved source"
    finally:
        files.close()


def test_oversize_nonregular_and_closed_project_rejected(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    (root / "large.txt").write_text("a" * (32 * 1024 + 1))
    (root / "directory").mkdir()
    files = ProjectFiles(root)
    try:
        for name in ("large.txt", "directory"):
            with pytest.raises(GuardError):
                files.read_text(name)
    finally:
        files.close()
    with pytest.raises(GuardError, match="CLOSED"):
        files.read_text("large.txt")
