import io
import tarfile

from demo.backend.build_runner import build_context


def test_build_context_omits_private_files_and_extended_host_metadata(tmp_path):
    (tmp_path / "demo/backend").mkdir(parents=True)
    (tmp_path / "tests/backend").mkdir(parents=True)
    (tmp_path / "demo/backend/Dockerfile").write_text("FROM python:3.12-slim\n")
    (tmp_path / "tests/backend/requirements-dev.lock").write_text("pytest==9.1.1\n")
    (tmp_path / ".env").write_text("DECLARED_SYNTHETIC_PRIVATE_MARKER=not-a-real-key\n")
    data = build_context(tmp_path)
    assert data.startswith(b"Dockerfile\x00")
    assert b"DECLARED_SYNTHETIC_PRIVATE_MARKER" not in data
    assert b"@PaxHeader" not in data
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        assert archive.getnames() == [
            "Dockerfile",
            "tests/backend/requirements-dev.lock",
        ]
        assert all(member.uid == 0 and member.uname == "" for member in archive)
