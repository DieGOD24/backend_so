"""Shortest Job First scheduling algorithm (non-preemptive)."""

from __future__ import annotations

from typing import Iterable

from ..pcb import PCB
from ..queues import ReadyQueue
from .base import SchedulingAlgorithm, SchedulingDecision


class SJFAlgorithm(SchedulingAlgorithm):
    """Non-preemptive SJF: dispatches the smallest remaining burst."""

    name = "sjf"

    def reset(self) -> None:
        """Reset algorithm state between runs."""
        # SJF uses no additional state yet.
        return None

    def prime(self, ready_queue: ReadyQueue, jobs: Iterable[PCB]) -> None:
        """Load all available jobs before the simulation starts."""
        ready_queue.extend(sorted(jobs, key=lambda pcb: pcb.burst_time))

    def next_tick(
        self,
        *,
        current_time: int,  # noqa: ARG002
        running: PCB | None,
        ready_queue: ReadyQueue,
    ) -> SchedulingDecision:
        """Pick the job with the shortest remaining burst."""
        if running:
            return SchedulingDecision(next_process=running)

        if len(ready_queue) == 0:
            return SchedulingDecision(next_process=None)

        # Choose the PCB with the smallest remaining burst time.
        shortest = min(ready_queue, key=lambda pcb: pcb.remaining_time)

        # Rebuild the queue without the selected PCB.
        buffer = []
        while len(ready_queue) > 0:
            candidate = ready_queue.dequeue()
            if candidate is shortest:
                continue
            buffer.append(candidate)
        ready_queue.extend(buffer)

        return SchedulingDecision(next_process=shortest)
