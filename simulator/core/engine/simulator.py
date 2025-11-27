"""Dispatcher for CPU scheduling simulation with optional I/O blocking."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

from .algorithms.base import SchedulingAlgorithm
from .metrics import SimulationMetrics
from .pcb import PCB
from .queues import BlockedQueue, ReadyQueue
from .states import ProcessState


@dataclass
class SimulationConfig:
    """Shared configuration for the simulator and algorithms."""

    algorithm: SchedulingAlgorithm
    time_slice: int | None = None
    max_time: int | None = None
    io_enabled: bool = True
    io_interval_mean: float = 5.0
    io_interval_stddev: float = 1.5
    io_duration_mean: float = 3.0
    io_duration_stddev: float = 1.0
    io_max_events: int | None = None


class SchedulerSimulator:
    """Coordinates queues, algorithm decisions and metrics in a discrete-time run."""

    def __init__(self, config: SimulationConfig) -> None:
        self.config = config
        self.ready_queue = ReadyQueue()
        self.blocked_queue = BlockedQueue()
        self.clock: int = 0
        self.completed: List[PCB] = []
        self._jobs: list[PCB] = []

        # Timeline para la UI de Django: lista de segmentos
        # {'t': tiempo_inicio, 'pid': int|None, 'evento': 'run'|'idle', 'dur': int}
        self.timeline: list[dict] = []

    def load_jobs(self, jobs: Sequence[PCB] | Iterable[PCB]) -> None:
        """Reset internal state and register the PCBs to simulate."""
        self.clock = 0
        self.ready_queue = ReadyQueue()
        self.blocked_queue = BlockedQueue()
        self.completed = []
        self.timeline = []
        self._jobs = list(jobs)
        self._jobs.sort(key=lambda pcb: pcb.arrival_time)

        for job in self._jobs:
            job.prepare_io_schedule(
                interval_mean=self.config.io_interval_mean,
                interval_stddev=self.config.io_interval_stddev,
                duration_mean=self.config.io_duration_mean,
                duration_stddev=self.config.io_duration_stddev,
                max_events=self.config.io_max_events,
                enabled=self.config.io_enabled and job.metadata.get("io_enabled", True),
            )

    def run(self) -> SimulationMetrics:
        """
        Execute the simulation using the configured algorithm.
        Returns SimulationMetrics; los PCBs finales quedan en self.completed
        y la línea de tiempo en self.timeline.
        """
        if not self._jobs:
            return SimulationMetrics()

        algorithm = self.config.algorithm
        if self.config.time_slice is not None and hasattr(algorithm, "quantum"):
            try:
                algorithm.quantum = self.config.time_slice
            except Exception:
                # Si el algoritmo no permite cambiar el quantum, ignoramos.
                pass
        algorithm.reset()

        total_jobs = len(self._jobs)
        jobs_pending: list[PCB] = list(self._jobs)
        running: PCB | None = None
        context_switches = 0
        busy_time = 0

        # Load jobs that arrive at time 0 through the algorithm's priming hook.
        initial_jobs: list[PCB] = []
        while jobs_pending and jobs_pending[0].arrival_time <= self.clock:
            job = jobs_pending.pop(0)
            job.set_state(ProcessState.READY)
            initial_jobs.append(job)
        if initial_jobs:
            algorithm.prime(self.ready_queue, initial_jobs)

        while len(self.completed) < total_jobs:
            if self.config.max_time is not None and self.clock >= self.config.max_time:
                break

            # Enqueue jobs that have just arrived.
            while jobs_pending and jobs_pending[0].arrival_time <= self.clock:
                job = jobs_pending.pop(0)
                job.set_state(ProcessState.READY)
                self.ready_queue.enqueue(job)

            # Advance blocked processes and return them to the ready queue when I/O completes.
            if len(self.blocked_queue) > 0:
                unblock: list[PCB] = []
                for _ in range(len(self.blocked_queue)):
                    blocked = self.blocked_queue.dequeue()
                    if blocked is None:
                        continue
                    blocked.tick_io()
                    if blocked.io_remaining_time is None:
                        unblock.append(blocked)
                    else:
                        self.blocked_queue.enqueue(blocked)
                if unblock:
                    for pcb in unblock:
                        pcb.set_state(ProcessState.READY)
                    self.ready_queue.extend(unblock)

            # If the CPU is idle and no jobs are ready, jump to the next arrival.
            if running is None and len(self.ready_queue) == 0:
                if len(self.blocked_queue) > 0:
                    # CPU ociosa 1 tick
                    self.timeline.append(
                        {"t": self.clock, "pid": None, "evento": "idle", "dur": 1}
                    )
                    self.clock += 1
                    continue
                if jobs_pending:
                    next_time = max(self.clock + 1, jobs_pending[0].arrival_time)
                    if next_time > self.clock:
                        self.timeline.append(
                            {
                                "t": self.clock,
                                "pid": None,
                                "evento": "idle",
                                "dur": next_time - self.clock,
                            }
                        )
                    self.clock = next_time
                    continue
                # Nothing left to do.
                break

            decision = algorithm.next_tick(
                current_time=self.clock,
                running=running,
                ready_queue=self.ready_queue,
            )

            if decision.preempt_current and running is not None and running is not decision.next_process:
                running.set_state(ProcessState.READY)
                self.ready_queue.enqueue(running)
                running = None

            if decision.next_process is not None and decision.next_process is not running:
                previous_pid = running.pid if running else None
                running = decision.next_process
                if running.start_time is None:
                    running.start_time = self.clock
                    running.response_time = self.clock - running.arrival_time
                if running.pid != previous_pid:
                    context_switches += 1

            # Ejecutamos un tick de CPU si hay proceso
            if running is not None:
                # Guardar en timeline este tick de ejecución
                self.timeline.append(
                    {"t": self.clock, "pid": running.pid, "evento": "run", "dur": 1}
                )

                running.set_state(ProcessState.RUNNING)
                running.consume(1)
                busy_time += 1
                blocked_now, _duration = running.io_request_due()
                if blocked_now:
                    running.set_state(ProcessState.BLOCKED)
                    self.blocked_queue.enqueue(running)
                    running = None

            self.clock += 1

            if running is not None and running.remaining_time == 0:
                running.finish_time = self.clock
                running.turnaround_time = running.finish_time - running.arrival_time
                running.waiting_time = running.turnaround_time - running.burst_time
                running.set_state(ProcessState.TERMINATED)
                self.completed.append(running)
                running = None

        metrics = SimulationMetrics.from_pcbs(self.completed)
        if self.clock > 0:
            metrics.throughput = len(self.completed) / self.clock
            metrics.cpu_utilization = busy_time / self.clock
        metrics.context_switches = context_switches
        return metrics
