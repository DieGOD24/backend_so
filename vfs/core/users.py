from dataclasses import dataclass
@dataclass
class Usuario:
    nombre: str
    uid: int
    grupo: str
DEFAULT_USERS = {
    "root": Usuario("root", 0, "root"),
    "usuario1": Usuario("usuario1", 1001, "usuarios"),
    "usuario2": Usuario("usuario2", 1002, "usuarios"),
}
