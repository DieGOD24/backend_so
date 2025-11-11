from .pcb import PCB
from .metrics import calcular_metricas
class Planificador:
    """FCFS, RR y SJF (no expropiativo)"""
    def _init_pcbs(self, procesos):
        return [PCB(pid=p['pid'], llegada=p['llegada'], rafaga=p['rafaga'],
                    prioridad=p.get('prioridad',0), usuario=p.get('usuario','root')) for p in procesos]
    def fcfs(self, procesos):
        """
        Macroalgoritmo FCFS
        1. Ordenar procesos por tiempo de llegada
        2. Ejecutar cada proceso hasta completar su ráfaga CPU
        3. No hay interrupciones por tiempo
        4. Calcular métricas al final
        """
        pcbs = self._init_pcbs(procesos)
        pcbs.sort(key=lambda p: p.llegada)
        t = 0; timeline = []
        for p in pcbs:
            if t < p.llegada:
                timeline.append({'t': t, 'evento':'CPU ociosa', 'dur': p.llegada - t})
                t = p.llegada
            p.inicio = t
            p.espera = max(0, p.inicio - p.llegada)
            timeline.append({'t': t, 'pid': p.pid, 'evento':'run', 'dur': p.rafaga})
            t += p.rafaga
            p.pc = p.rafaga
            p.fin = t
            p.estado = 'Terminado'
        return calcular_metricas(pcbs, timeline)
    def round_robin(self, procesos, quantum=2):
        """
        Macroalgoritmo Round Robin
        1. Cola circular de procesos listos
        2. Asignar quantum a cada uno
        3. Si no termina, vuelve a la cola
        4. Repetir hasta que todos terminen
        """
        pcbs = self._init_pcbs(procesos)
        t = 0; timeline = []; ready = []
        not_arrived = sorted(pcbs, key=lambda p: p.llegada)
        current = None
        def enqueue_arrivals():
            nonlocal ready, not_arrived, t
            while not_arrived and not_arrived[0].llegada <= t:
                q = not_arrived.pop(0)
                q.estado = 'Listo'
                ready.append(q)
        while not_arrived or ready or current:
            enqueue_arrivals()
            if not current:
                if ready:
                    current = ready.pop(0)
                    if current.inicio is None:
                        current.inicio = t
                        current.espera += max(0, t - current.llegada)
                else:
                    if not_arrived:
                        idle = not_arrived[0].llegada - t
                        if idle > 0:
                            timeline.append({'t': t, 'evento':'CPU ociosa', 'dur': idle})
                            t += idle
                            enqueue_arrivals()
                    continue
            run = min(quantum, current.restante)
            timeline.append({'t': t, 'pid': current.pid, 'evento':'run', 'dur': run})
            t += run
            current.restante -= run
            enqueue_arrivals()
            if current.restante == 0:
                current.fin = t
                current.estado = 'Terminado'
                current = None
            else:
                ready.append(current)
                current = None
        return calcular_metricas(pcbs, timeline)
    def sjf(self, procesos):
        """
        Macroalgoritmo SJF (no expropiativo)
        1. Entre los disponibles, elegir ráfaga más corta
        2. Ejecutar completo
        3. Repetir
        """
        pcbs = self._init_pcbs(procesos)
        t = 0; timeline = []; ready = []
        not_arrived = sorted(pcbs, key=lambda p: p.llegada)
        def enqueue_arrivals():
            nonlocal ready, not_arrived, t
            while not_arrived and not_arrived[0].llegada <= t:
                ready.append(not_arrived.pop(0))
        while ready or not_arrived:
            enqueue_arrivals()
            if not ready:
                nxt = not_arrived.pop(0)
                if t < nxt.llegada:
                    timeline.append({'t': t, 'evento':'CPU ociosa', 'dur': nxt.llegada - t})
                    t = nxt.llegada
                ready.append(nxt)
            ready.sort(key=lambda p: p.rafaga)
            p = ready.pop(0)
            p.inicio = t
            p.espera = max(0, p.inicio - p.llegada)
            timeline.append({'t': t, 'pid': p.pid, 'evento':'run', 'dur': p.rafaga})
            t += p.rafaga
            p.fin = t
            p.estado = 'Terminado'
        return calcular_metricas(pcbs, timeline)
