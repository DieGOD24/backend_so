from dataclasses import dataclass, field
from typing import Dict, Optional
from .users import Usuario
@dataclass
class Nodo:
    nombre: str
    propietario: Usuario
    permisos: str = "rw-r--r--"
@dataclass
class Archivo(Nodo):
    contenido: str = ""
    tamanio: int = 0
@dataclass
class Directorio(Nodo):
    hijos: Dict[str, Nodo] = field(default_factory=dict)
    def add(self, nodo: Nodo):
        self.hijos[nodo.nombre] = nodo
    def get(self, name: str) -> Optional[Nodo]:
        return self.hijos.get(name)
