"""Single worker, deduplicated queue, manual idle trigger and cooperative pause."""

import threading
from collections import deque


class Scheduler:
    def __init__(self, execute):
        self.execute = execute
        self._queue = deque()
        self._queued: set[str] = set()
        self._lock = threading.RLock()
        self._thread: threading.Thread | None = None
        self.paused = True
        self.current: str | None = None

    def enqueue(self, run_id: str) -> None:
        with self._lock:
            if run_id not in self._queued and run_id != self.current:
                self._queue.append(run_id)
                self._queued.add(run_id)
            if not self.paused:
                self._start()

    def _start(self) -> None:
        if not self._thread or not self._thread.is_alive():
            self._thread = threading.Thread(
                target=self._drain, name="devguard-repair", daemon=True
            )
            self._thread.start()

    def enter_idle(self) -> None:
        with self._lock:
            self.paused = False
            self._start()

    def pause(self) -> str | None:
        with self._lock:
            self.paused = True
            return self.current

    def _drain(self) -> None:
        while True:
            with self._lock:
                if self.paused or not self._queue:
                    self.current = None
                    # Mark idle while holding lock so an enqueue cannot strand work.
                    self._thread = None
                    return
                self.current = self._queue.popleft()
                self._queued.remove(self.current)
                current = self.current
            self.execute(current)
            with self._lock:
                self.current = None

    def join(self, timeout: float = 5) -> None:
        thread = self._thread
        if thread:
            thread.join(timeout)

    def stopped(self) -> bool:
        with self._lock:
            return self._thread is None or not self._thread.is_alive()
