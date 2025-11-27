"""Abstractions shared across all scheduling algorithms."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol

from ..pcb import PCB
from ..queues import ReadyQueue


@dataclass(slots=True)
class SchedulingDecision:
    """Represents the outcome of a scheduling step."""

    next_process: PCB | None
    preempt_current: bool = False  # "preemptar" = interrumpir el proceso actual
    timeslice: int | None = None
    notes: str | None = None


class SchedulingAlgorithm(Protocol):
    """
    Expected behaviour for every scheduling algorithm.
    """

    name: str

    def reset(self) -> None:
        """Reset internal state before a new simulation run."""
        raise NotImplementedError

    def prime(self, ready_queue: ReadyQueue, jobs: Iterable[PCB]) -> None:
        """Load the ready queue before starting the simulation loop."""
        raise NotImplementedError

    def next_tick(
        self,
        *,
        current_time: int,
        running: PCB | None,
        ready_queue: ReadyQueue,
    ) -> SchedulingDecision:
        """Return the next scheduling decision."""
        raise NotImplementedError
