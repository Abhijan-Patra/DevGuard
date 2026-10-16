"""Explicit-file snapshots; no recursive copying of a developer's home/repository."""

import hashlib
import json
import os
import shutil
import stat
import tempfile
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from .contracts import GuardPort, ProjectSpec, RepairError

MAX_FILE_BYTES = 128 * 1024
MAX_TOTAL_BYTES = 512 * 1024
PROTECTED = {".git", ".codex", ".devguard", "trusted_tests", "tests", "node_modules"}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_relative(name: str) -> str:
    p = PurePosixPath(name)
    if (
        not name
        or p.is_absolute()
        or "\\" in name
        or "\x00" in name
        or any(part in {"", ".", ".."} for part in name.split("/"))
        or any(part in PROTECTED or part.startswith(".env") for part in p.parts)
        or p.suffix.lower() in {".key", ".pem", ".p12", ".sqlite", ".db"}
    ):
        raise RepairError("PATH_DENIED")
    return name


def checked_file(root: Path, name: str) -> Path:
    safe_relative(name)
    current = root
    for part in PurePosixPath(name).parts:
        current = current / part
        if current.is_symlink():
            raise RepairError("SYMLINK_DENIED")
    try:
        info = current.stat()
    except OSError:
        raise RepairError("SOURCE_UNAVAILABLE") from None
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise RepairError("FILE_TYPE_DENIED")
    if info.st_size > MAX_FILE_BYTES:
        raise RepairError("SOURCE_TOO_LARGE")
    return current


def read_source(root: Path, name: str) -> bytes:
    safe_relative(name)
    # Anchor every parent lookup to directory descriptors, rejecting intermediate
    # symlinks as well as a symlink leaf. Do not validate a path then follow it later.
    descriptor = None
    fd = None
    try:
        descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        parts = PurePosixPath(name).parts
        for part in parts[:-1]:
            following = os.open(
                part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor
            )
            os.close(descriptor)
            descriptor = following
        fd = os.open(
            parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=descriptor
        )
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise RepairError("FILE_TYPE_DENIED")
        if info.st_size > MAX_FILE_BYTES:
            raise RepairError("SOURCE_TOO_LARGE")
        data = os.read(fd, MAX_FILE_BYTES + 1)
    except OSError:
        # Keep the exact reason for a pre-existing symlink without reflecting paths.
        checked_file(root, name)
        raise RepairError("SOURCE_UNAVAILABLE") from None
    finally:
        if fd is not None:
            os.close(fd)
        if descriptor is not None:
            os.close(descriptor)
    if len(data) > MAX_FILE_BYTES:
        raise RepairError("SOURCE_TOO_LARGE")
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        raise RepairError("BINARY_SOURCE_DENIED") from None
    return data


def revision(files: dict[str, bytes]) -> str:
    return digest(json.dumps({k: digest(v) for k, v in sorted(files.items())}).encode())


@dataclass
class Snapshot:
    directory: Path
    originals: dict[str, bytes] = field(repr=False)
    base_revision: str
    source: Path

    def close(self) -> None:
        shutil.rmtree(self.directory)
        self.originals.clear()


def capture(
    spec: ProjectSpec, runtime_root: Path, guard: GuardPort | None = None
) -> Snapshot:
    root = spec.root
    if root.is_symlink() or not root.is_dir() or root.resolve() != root:
        raise RepairError("PROJECT_ROOT_DENIED")
    if not spec.source_files or len(spec.source_files) > 32:
        raise RepairError("SOURCE_SCOPE_DENIED")
    if not set(spec.writable_files).issubset(spec.source_files):
        raise RepairError("WRITE_SCOPE_DENIED")
    originals = {name: read_source(root, name) for name in spec.source_files}
    if sum(map(len, originals.values())) > MAX_TOTAL_BYTES:
        raise RepairError("SOURCE_TOO_LARGE")
    if guard is not None:
        for data in originals.values():
            text = data.decode("utf-8")
            if guard.sanitize(text, purpose="snapshot_source") != text:
                raise RepairError("SOURCE_REQUIRES_SANITIZATION")
    # Read again to reject a moving source snapshot, including saved uncommitted edits.
    if any(read_source(root, n) != b for n, b in originals.items()):
        raise RepairError("SOURCE_CHANGED")
    if runtime_root.is_symlink() or runtime_root.resolve() != runtime_root:
        raise RepairError("RUNTIME_ROOT_DENIED")
    runtime_root.mkdir(mode=0o700, parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="repair-", dir=runtime_root))
    directory.chmod(0o700)
    source = directory / "source"
    source.mkdir()
    for name, data in originals.items():
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        path.chmod(0o644)
    return Snapshot(directory, originals, revision(originals), source)
