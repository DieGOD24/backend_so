from dataclasses import dataclass
@dataclass
class Resultado:
    timeline: list
    completed: list
    avg_wait: float
    avg_turnaround: float
    makespan: int
def calcular_metricas(pcbs, timeline):
    completados = [p for p in pcbs if p.fin is not None]
    if not completados:
        return Resultado(timeline, [], 0.0, 0.0, 0)
    waits = [p.espera for p in completados]
    turnarounds = [(p.fin - p.llegada) for p in completados]
    makespan = max(p.fin for p in completados)
    return Resultado(
        timeline,
        [p.__dict__ for p in completados],
        sum(waits)/len(waits),
        sum(turnarounds)/len(turnarounds),
        makespan
    )
