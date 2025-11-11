from dataclasses import dataclass, field
ESTADOS = ('Nuevo','Listo','Ejecutando','Bloqueado','Terminado')
@dataclass
class PCB:
    pid: int
    estado: str = 'Nuevo'
    pc: int = 0
    llegada: int = 0
    rafaga: int = 0
    prioridad: int = 0
    usuario: str = 'root'
    inicio: int = None
    fin: int = None
    espera: int = 0
    restante: int = field(default=0)
    def __post_init__(self):
        if self.restante == 0:
            self.restante = self.rafaga
