"""Descriptor-anchored reads for approved projects; no model-selected roots."""

import contextlib
import os
from pathlib import Path, PurePosixPath
import stat

from devguard.guard.engine import GuardError
from devguard.schemas.guard import MAX_TEXT_BYTES

PROTECTED_PARTS = {".git", ".devguard", ".ssh", ".aws", ".codex", "trusted_tests"}
PROTECTED_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}


class ProjectFiles:
    """Created by the trusted operator, then passed to a scoped tool registry."""

    def __init__(self, root):
        root = Path(root).resolve(strict=True)
        if root in {Path("/"), Path.home(), Path(root.anchor)}:
            raise GuardError("PROJECT_ROOT_TOO_BROAD", 403)
        self._windows_anchor = None
        if os.name == 'nt':
            from devguard.windows import anchored_directory
            self._windows_anchor = anchored_directory(root)
            try:
                self._windows_anchor.__enter__()
            except OSError:
                raise GuardError('SOURCE_READ_DENIED', 403) from None
            self._root_fd = root
        else:
            self._root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)

    def close(self):
        if self._root_fd is not None:
            if self._windows_anchor is not None:
                self._windows_anchor.__exit__(None, None, None)
                self._windows_anchor = None
            else:
                os.close(self._root_fd)
            self._root_fd = None

    def read_text(self, relative):
        if self._root_fd is None:
            raise GuardError("PROJECT_CLOSED")
        if not relative or "\\" in relative or "\0" in relative:
            raise GuardError("PATH_DENIED", 403)
        path = PurePosixPath(relative)
        if path.is_absolute() or ".." in path.parts or len(path.parts) > 32:
            raise GuardError("PATH_DENIED", 403)
        if any(part.casefold() in PROTECTED_PARTS or part.casefold() == ".env" or part.casefold().startswith(".env.")
               for part in path.parts) or path.suffix.lower() in PROTECTED_SUFFIXES:
            raise GuardError("PROTECTED_PATH", 403)
        from devguard.windows import relative_parts
        try:
            relative_parts(relative)
        except OSError:
            raise GuardError('PATH_DENIED', 403) from None
        if os.name == 'nt':
            from devguard.windows import read_source
            try:
                return read_source(self._root_fd, relative, MAX_TEXT_BYTES).decode('utf-8', errors='strict')
            except (OSError, UnicodeError):
                raise GuardError('SOURCE_READ_DENIED', 403) from None
        descriptors = []
        try:
            parent = self._root_fd
            for part in path.parts[:-1]:
                parent = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
                descriptors.append(parent)
            fd = os.open(path.parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
            descriptors.append(fd)
            before = os.fstat(fd)
            if not stat.S_ISREG(before.st_mode):
                raise GuardError("REGULAR_SOURCE_FILE_REQUIRED", 403)
            if before.st_size > MAX_TEXT_BYTES:
                raise GuardError("SOURCE_TOO_LARGE", 413)
            raw = os.read(fd, MAX_TEXT_BYTES + 1)
            after = os.fstat(fd)
            if (before.st_mtime_ns, before.st_size) != (after.st_mtime_ns, after.st_size):
                raise GuardError("SOURCE_CHANGED")
            if len(raw) != after.st_size:
                raise GuardError("SOURCE_READ_INCOMPLETE")
            if len(raw) > MAX_TEXT_BYTES:
                raise GuardError("SOURCE_TOO_LARGE", 413)
            return raw.decode("utf-8", errors="strict")
        except (OSError, UnicodeError, IndexError):
            raise GuardError("SOURCE_READ_DENIED", 403) from None
        finally:
            for descriptor in reversed(descriptors):
                with contextlib.suppress(OSError):
                    os.close(descriptor)
