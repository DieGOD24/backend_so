from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List

from .engine.metrics import SimulationMetrics
from .engine.simulator import SchedulerSimulator
from .engine.pcb import PCB


@dataclass
class Resultado:
    timeline: list[dict[str, Any]]
    completed: list[dict[str, Any]]
    avg_wait: float
    avg_turnaround: float
    avg_response: float
    makespan: int
    throughput: float | None
    cpu_utilization: float | None
    context_switches: int


def construir_resultado(
    sim: SchedulerSimulator,
    metrics: SimulationMetrics,
) -> Resultado:
    """
    Convierte los PCBs + métricas agregadas en un objeto Resultado
    compatible con tu template de Django.
    """
    # PCBs completados
    pcbs: List[PCB] = list(sim.completed)

    # Lista de procesos completados con info útil
    completed_info: list[dict[str, Any]] = []
    for pcb in pcbs:
        completed_info.append(
            {
                "pid": pcb.pid,
                "arrival_time": pcb.arrival_time,
                "burst_time": pcb.burst_time,
                "start_time": pcb.start_time,
                "finish_time": pcb.finish_time,
                "waiting_time": pcb.waiting_time,
                "turnaround_time": pcb.turnaround_time,
                "response_time": pcb.response_time,
            }
        )

    # Promedios a partir de metrics.processes
    waits = [
        p.waiting_time for p in metrics.processes if p.waiting_time is not None
    ]
    turns = [
        p.turnaround_time for p in metrics.processes if p.turnaround_time is not None
    ]
    resps = [
        p.response_time for p in metrics.processes if p.response_time is not None
    ]

    avg_wait = sum(waits) / len(waits) if waits else 0.0
    avg_turn = sum(turns) / len(turns) if turns else 0.0
    avg_resp = sum(resps) / len(resps) if resps else 0.0

    # Makespan: último tiempo de finalización
    makespan = 0
    if pcbs:
        finishes = [pcb.finish_time for pcb in pcbs if pcb.finish_time is not None]
        if finishes:
            makespan = max(finishes)

    return Resultado(
        timeline=sim.timeline,
        completed=completed_info,
        avg_wait=avg_wait,
        avg_turnaround=avg_turn,
        avg_response=avg_resp,
        makespan=makespan,
        throughput=metrics.throughput,
        cpu_utilization=metrics.cpu_utilization,
        context_switches=metrics.context_switches,
    )
