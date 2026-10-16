"""One-file candidates for an atomic first implementation; originals stay in memory."""

import difflib

try:
    import fcntl
except ImportError:
    fcntl = None
import os
import tempfile
import threading
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from .contracts import GuardPort, ProjectSpec, RepairError
from .workspace import (
    MAX_FILE_BYTES,
    Snapshot,
    checked_file,
    digest,
    read_source,
    revision,
)


@dataclass
class Candidate:
    candidate_id: str
    run_id: str
    base_revision: str
    candidate_hash: str
    diff: str = field(repr=False)
    originals: dict[str, bytes] = field(repr=False)
    replacements: dict[str, bytes] = field(repr=False)
    state: str = "READY_FOR_REVIEW"
    idempotency_key: str | None = None

    def view(self) -> dict:
        return {
            "candidate_id": self.candidate_id,
            "run_id": self.run_id,
            "base_revision": self.base_revision,
            "candidate_hash": self.candidate_hash,
            "diff": self.diff,
            "state": self.state,
            "verification": "PASS",
            "base_hashes": {n: digest(b) for n, b in self.originals.items()},
        }


def replace_in_snapshot(
    snapshot: Snapshot, spec: ProjectSpec, path: str, content: str, expected_hash: str
) -> None:
    if path not in spec.writable_files or path not in snapshot.originals:
        raise RepairError("WRITE_DENIED")
    data = content.encode("utf-8")
    if len(data) > MAX_FILE_BYTES:
        raise RepairError("PATCH_TOO_LARGE")
    current = read_source(snapshot.source, path)
    if digest(current) != expected_hash:
        raise RepairError("STALE_SANDBOX")
    checked_file(snapshot.source, path).write_bytes(data)


def build_candidate(
    snapshot: Snapshot, spec: ProjectSpec, run_id: str, guard: GuardPort
) -> Candidate:
    edits = {}
    diff = ""
    for name, original in snapshot.originals.items():
        updated = read_source(snapshot.source, name)
        if updated == original:
            continue
        if name not in spec.writable_files:
            raise RepairError("WRITE_DENIED")
        edits[name] = updated
        diff += "".join(
            difflib.unified_diff(
                original.decode().splitlines(keepends=True),
                updated.decode().splitlines(keepends=True),
                fromfile="a/" + name,
                tofile="b/" + name,
            )
        )
    if len(edits) != 1:
        raise RepairError("SINGLE_FILE_PATCH_REQUIRED")
    # Altered diff bytes cannot be offered as an applicable, verified candidate.
    if guard.sanitize(diff, purpose="patch_export") != diff:
        raise RepairError("PATCH_EXPORT_HELD")
    return Candidate(
        "patch-" + uuid.uuid4().hex,
        run_id,
        snapshot.base_revision,
        revision(edits),
        diff,
        dict(snapshot.originals),
        edits,
    )


class PatchStore:
    def __init__(self):
        self.candidates: dict[str, Candidate] = {}
        self._lock = threading.RLock()

    def get(self, candidate_id: str) -> Candidate:
        try:
            return self.candidates[candidate_id]
        except KeyError:
            raise RepairError("NOT_FOUND") from None

    def reject(self, candidate_id: str) -> Candidate:
        with self._lock:
            candidate = self.get(candidate_id)
            if candidate.state == "APPLIED":
                raise RepairError("PATCH_ALREADY_APPLIED")
            candidate.state = "REJECTED"
            candidate.replacements.clear()
            candidate.originals.clear()
            return candidate

    def apply(
        self,
        candidate_id: str,
        spec: ProjectSpec,
        *,
        expected_hash: str,
        expected_base: str,
        idempotency_key: str,
        approved: bool,
    ) -> Candidate:
        with self._lock:
            candidate = self.get(candidate_id)
            if not approved or not 1 <= len(idempotency_key) <= 128:
                raise RepairError("OPERATOR_APPROVAL_REQUIRED")
            if (
                expected_hash != candidate.candidate_hash
                or expected_base != candidate.base_revision
            ):
                raise RepairError("CANDIDATE_CONFLICT")
            if candidate.state == "APPLIED":
                if candidate.idempotency_key == idempotency_key:
                    return candidate
                raise RepairError("PATCH_ALREADY_APPLIED")
            if candidate.state != "READY_FOR_REVIEW":
                raise RepairError("PATCH_NOT_READY")
            lock_dir = spec.root / ".devguard"
            if lock_dir.is_symlink():
                raise RepairError("SYMLINK_DENIED")
            lock_dir.mkdir(mode=0o700, exist_ok=True)
            flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
            fd = os.open(lock_dir / "apply.lock", flags, 0o600)
            with os.fdopen(fd, "w") as lock:
                if fcntl is not None:
                    fcntl.flock(lock, fcntl.LOCK_EX)
                try:
                    live = {
                        name: read_source(spec.root, name)
                        for name in candidate.originals
                    }
                    if live != candidate.originals:
                        raise RepairError("STALE_SOURCE")
                    if revision(candidate.replacements) != candidate.candidate_hash:
                        raise RepairError("CANDIDATE_CONFLICT")
                    if len(candidate.replacements) != 1:
                        raise RepairError("SINGLE_FILE_PATCH_REQUIRED")
                    name, data = next(iter(candidate.replacements.items()))
                    if name not in spec.writable_files:
                        raise RepairError("WRITE_DENIED")
                    target = checked_file(spec.root, name)
                    mode = target.stat().st_mode & 0o777
                    temporary = None
                    try:
                        with tempfile.NamedTemporaryFile(
                            dir=target.parent, delete=False
                        ) as handle:
                            temporary = Path(handle.name)
                            handle.write(data)
                            handle.flush()
                            os.fsync(handle.fileno())
                        temporary.chmod(mode)
                        if read_source(spec.root, name) != candidate.originals[name]:
                            raise RepairError("STALE_SOURCE")
                        os.replace(temporary, target)
                    finally:
                        if temporary is not None:
                            temporary.unlink(missing_ok=True)
                    candidate.state = "APPLIED"
                    candidate.idempotency_key = idempotency_key
                except RepairError as error:
                    if error.code in {
                        "STALE_SOURCE",
                        "SOURCE_UNAVAILABLE",
                        "SYMLINK_DENIED",
                        "FILE_TYPE_DENIED",
                    }:
                        candidate.state = "OBSOLETE"
                    raise
            return candidate
