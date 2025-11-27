"""Metrics models produced by the scheduler simulator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List


@dataclass(slots=True)
class ProcessMetrics:
    """Holds the canonical metrics for a single process."""

    pid: int
    waiting_time: float | None = None
    turnaround_time: float | None = None  # total time from arrival to completion
    response_time: float | None = None


@dataclass(slots=True)
class SimulationMetrics:
    """Aggregated metrics from a scheduler run."""

    processes: List[ProcessMetrics] = field(default_factory=list)
    throughput: float | None = None
    cpu_utilization: float | None = None
    context_switches: int = 0

    def add_process_metrics(self, metrics: ProcessMetrics) -> None:
        """Collect metrics for a single process."""
        self.processes.append(metrics)

    @classmethod
    def from_pcbs(cls, pcbs: Iterable["PCB"]) -> "SimulationMetrics":  # type: ignore
        """
        Build metrics from the final PCB state.
        """
        from .pcb import PCB  # pylint: disable=cyclic-import

        metrics = cls()
        finished: List[PCB] = list(pcbs)

        for pcb in finished:
            if pcb.finish_time is None:
                # Skip processes that never finished.
                continue
            waiting = pcb.waiting_time
            if waiting is None and pcb.turnaround_time is not None:
                waiting = pcb.turnaround_time - pcb.burst_time
            turnaround = pcb.turnaround_time
            if turnaround is None:
                turnaround = pcb.finish_time - pcb.arrival_time
            response = pcb.response_time
            metrics.add_process_metrics(
                ProcessMetrics(
                    pid=pcb.pid,
                    waiting_time=waiting,
                    turnaround_time=turnaround,
                    response_time=response,
                )
            )

        return metrics