"""Simple queue helpers for the simulator."""

from __future__ import annotations

from collections import deque
from typing import Deque, Iterable, Iterator

from .pcb import PCB


class ProcessQueue:
    """Wrapper around `deque` to keep queue instrumentation in one place."""

    def __init__(self, *, name: str) -> None:
        self.name = name
        self._items: Deque[PCB] = deque()

    def enqueue(self, pcb: PCB) -> None:
        """Add a PCB to the queue."""
        self._items.append(pcb)

    def dequeue(self) -> PCB | None:
        """Remove and return the next PCB, or None when empty."""
        if not self._items:
            return None
        return self._items.popleft()

    def peek(self) -> PCB | None:
        """Return the next PCB without dequeuing it."""
        if not self._items:
            return None
        return self._items[0]

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[PCB]:
        return iter(self._items)

    def extend(self, items: Iterable[PCB]) -> None:
        """Bulk enqueue."""
        self._items.extend(items)


class ReadyQueue(ProcessQueue):
    """Queue that feeds the CPU."""

    def __init__(self) -> None:
        super().__init__(name="ready")


class BlockedQueue(ProcessQueue):
    """Queue for processes waiting on I/O or similar events."""

    def __init__(self) -> None:
        super().__init__(name="blocked")
