"""Round Robin scheduling algorithm with configurable quantum."""

from __future__ import annotations

from typing import Iterable

from ..pcb import PCB
from ..queues import ReadyQueue
from .base import SchedulingAlgorithm, SchedulingDecision


class RoundRobinAlgorithm(SchedulingAlgorithm):
    """Preemptive Round Robin: rotates processes after consuming the quantum."""

    name = "rr"

    def __init__(self, quantum: int) -> None:
        self.quantum = quantum
        self._current_pid: int | None = None
        self._dispatch_time: int = 0

    def reset(self) -> None:
        """Reset algorithm state between runs."""
        self._current_pid = None
        self._dispatch_time = 0

    def prime(self, ready_queue: ReadyQueue, jobs: Iterable[PCB]) -> None:
        """Initial load simply enqueues the jobs."""
        ready_queue.extend(sorted(jobs, key=lambda pcb: pcb.arrival_time))

    def next_tick(
        self,
        *,
        current_time: int,
        running: PCB | None,
        ready_queue: ReadyQueue,
    ) -> SchedulingDecision:
        """RR rotates processes after consuming the quantum."""
        if running and running.pid != self._current_pid:
            # Process was (re)dispatched outside of our bookkeeping window.
            self._current_pid = running.pid
            self._dispatch_time = current_time

        should_preempt = False
        next_proc: PCB | None = running

        if running is None:
            next_proc = ready_queue.dequeue()
            if next_proc:
                self._current_pid = next_proc.pid
                self._dispatch_time = current_time
        else:
            time_in_cpu = current_time - self._dispatch_time
            if time_in_cpu >= self.quantum and len(ready_queue) > 0:
                should_preempt = True
                next_proc = ready_queue.dequeue()
                if next_proc:
                    self._current_pid = next_proc.pid
                    self._dispatch_time = current_time
                else:
                    self._current_pid = None

        return SchedulingDecision(
            next_process=next_proc,
            preempt_current=should_preempt,
            timeslice=self.quantum,
        )
