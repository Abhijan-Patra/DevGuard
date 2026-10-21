"""Bounded, non-preemptive inference admission on the existing app event loop."""

import asyncio
from contextlib import asynccontextmanager
import heapq
import time
from itertools import count


class QueueUnavailable(Exception):
    pass


class InferenceQueue:
    PRIORITIES = {"foreground": 0, "background": 10}

    def __init__(self, *, capacity=16):
        self.capacity = capacity
        self._condition = asyncio.Condition()
        self._sequence = count()
        self._waiting = []
        self._active = False
        self._closed = False
        self.last_foreground = time.monotonic()

    def status(self):
        return {
            "active": self._active,
            "foreground_waiting": sum(p == 0 for p, _, _ in self._waiting),
            "background_waiting": sum(p == 10 for p, _, _ in self._waiting),
            "capacity": self.capacity,
            "closed": self._closed,
        }

    async def close(self):
        async with self._condition:
            self._closed = True
            self._condition.notify_all()

    @asynccontextmanager
    async def slot(self, priority):
        if priority not in self.PRIORITIES:
            raise ValueError("Unknown inference priority")
        if priority == 'foreground':
            self.last_foreground = time.monotonic()
        ticket = (self.PRIORITIES[priority], next(self._sequence), object())
        async with self._condition:
            if self._closed or len(self._waiting) >= self.capacity:
                raise QueueUnavailable()
            heapq.heappush(self._waiting, ticket)
            try:
                await self._condition.wait_for(lambda: self._closed or (
                    not self._active and self._waiting[0] is ticket))
                if self._closed:
                    raise QueueUnavailable()
                heapq.heappop(self._waiting)
                self._active = True
            except BaseException:
                self._waiting.remove(ticket)
                heapq.heapify(self._waiting)
                self._condition.notify_all()
                raise
        try:
            yield
        finally:
            if priority == 'foreground':
                self.last_foreground = time.monotonic()
            async with self._condition:
                self._active = False
                self._condition.notify_all()
