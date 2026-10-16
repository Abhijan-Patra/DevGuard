"""Poll an explicit approved source manifest; debounce before creating an incident."""

import time

from devguard.repair.contracts import ProjectSpec, RepairError
from devguard.repair.workspace import checked_file


class SavedFileMonitor:
    def __init__(
        self, spec: ProjectSpec, signal: str, on_change, debounce_seconds: float = 2
    ):
        if signal not in spec.test_names:
            raise RepairError("TEST_DENIED")
        self.spec, self.signal, self.on_change = spec, signal, on_change
        self.debounce_seconds = debounce_seconds
        self._last = self._stats()
        self._changed_at: float | None = None

    def _stats(self) -> tuple:
        return tuple(
            (
                n,
                (s := checked_file(self.spec.root, n).stat()).st_mtime_ns,
                s.st_size,
                s.st_ino,
            )
            for n in self.spec.source_files
        )

    def tick(self, now: float | None = None) -> None:
        """Call from Mac 1's lifecycle; errors hold this project, never broaden its scope."""
        now = time.monotonic() if now is None else now
        current = self._stats()
        if current != self._last:
            self._last, self._changed_at = current, now
        elif (
            self._changed_at is not None
            and now - self._changed_at >= self.debounce_seconds
        ):
            self.on_change(self.spec.project_id, self.signal)
            self._changed_at = None
