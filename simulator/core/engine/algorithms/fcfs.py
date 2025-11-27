"""First-Come First-Served scheduling algorithm."""

from __future__ import annotations

from typing import Iterable

from ..pcb import PCB
from ..queues import ReadyQueue
from .base import SchedulingAlgorithm, SchedulingDecision


class FCFSAlgorithm(SchedulingAlgorithm):
    """Non-preemptive FCFS implementation."""

    name = "fcfs"

    def reset(self) -> None:
        """No internal state yet, but method provided for symmetry."""
        # Nothing to reset for FCFS.

    def prime(self, ready_queue: ReadyQueue, jobs: Iterable[PCB]) -> None:
        """Load jobs in arrival order."""
        ready_queue.extend(sorted(jobs, key=lambda pcb: pcb.arrival_time))

    def next_tick(
        self,
        *,
        current_time: int,  # noqa: ARG002
        running: PCB | None,
        ready_queue: ReadyQueue,
    ) -> SchedulingDecision:
        """FCFS always selects the head of the ready queue."""
        if running:
            return SchedulingDecision(next_process=running)

        next_proc = ready_queue.dequeue()
        return SchedulingDecision(next_process=next_proc)
