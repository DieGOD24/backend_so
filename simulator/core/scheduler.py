from __future__ import annotations

from typing import List, Dict, Any

from .engine.algorithms.fcfs import FCFSAlgorithm
from .engine.algorithms.sjf import SJFAlgorithm
from .engine.algorithms.rr import RoundRobinAlgorithm
from .engine.pcb import PCB
from .engine.simulator import SchedulerSimulator, SimulationConfig
from .metrics import Resultado, construir_resultado


class Planificador:
    """
    Fachada para usar el motor SchedulerSimulator desde Django.

    Recibe una lista de diccionarios:
      {"pid": 1, "llegada": 0, "rafaga": 5, "prioridad": 0, "usuario": "usuario1"}
    y devuelve un Resultado listo para el template.
    """

    def _pcbs_from_procesos(self, procesos: List[Dict[str, Any]]) -> list[PCB]:
        pcbs: list[PCB] = []
        for p in procesos:
            pid = int(p["pid"])
            llegada = int(p.get("llegada", 0))
            rafaga = int(p.get("rafaga", 0))
            prioridad = p.get("prioridad")
            usuario = p.get("usuario", "root")

            pcb = PCB(
                pid=pid,
                arrival_time=llegada,
                burst_time=rafaga,
                priority=prioridad,
                metadata={
                    "usuario": usuario,
                    # para simplificar la práctica, por defecto desactivamos I/O
                    "io_enabled": False,
                },
            )
            pcbs.append(pcb)
        return pcbs

    def _run(
        self,
        procesos: List[Dict[str, Any]],
        algoritmo: str,
        quantum: int | None = None,
    ) -> Resultado:
        pcbs = self._pcbs_from_procesos(procesos)

        if algoritmo == "fcfs":
            alg = FCFSAlgorithm()
        elif algoritmo == "sjf":
            alg = SJFAlgorithm()
        elif algoritmo == "rr":
            if quantum is None or quantum <= 0:
                quantum = 2
            alg = RoundRobinAlgorithm(quantum=quantum)
        else:
            raise ValueError(f"Algoritmo no soportado: {algoritmo}")

        config = SimulationConfig(
            algorithm=alg,
            time_slice=None,      # usamos el quantum del algoritmo tal cual
            max_time=None,
            io_enabled=False,     # I/O desactivado por ahora (lo puedes exponer en el form luego)
        )

        sim = SchedulerSimulator(config)
        sim.load_jobs(pcbs)
        metrics = sim.run()
        return construir_resultado(sim, metrics)

    # ---- Métodos públicos para la vista (mantienen la interfaz) ----

    def fcfs(self, procesos: List[Dict[str, Any]]) -> Resultado:
        return self._run(procesos, algoritmo="fcfs")

    def round_robin(self, procesos: List[Dict[str, Any]], quantum: int = 2) -> Resultado:
        return self._run(procesos, algoritmo="rr", quantum=quantum)

    def sjf(self, procesos: List[Dict[str, Any]]) -> Resultado:
        return self._run(procesos, algoritmo="sjf")
