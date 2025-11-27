from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from .permissions import PermissionSet


@dataclass(slots=True)
class User:
    """Usuario que interactúa con el sistema de archivos."""
    username: str
    home: str = "/"

    # Alias para ser compatible con tu código anterior (fs.usuario_actual.nombre)
    @property
    def nombre(self) -> str:
        return self.username


@dataclass
class FileSystemEntity:
    """Nodo base compartido por archivos y directorios."""
    name: str
    owner: User
    permissions: PermissionSet
    parent: "Directory | None" = None

    def path(self) -> str:
        """Devuelve la ruta absoluta de este nodo."""
        if self.parent is None:
            return "/"
        if self.parent.parent is None:
            return f"/{self.name}"
        return f"{self.parent.path().rstrip('/')}/{self.name}"


@dataclass
class File(FileSystemEntity):
    """Archivo con contenido de texto."""
    content: str = ""


@dataclass
class Directory(FileSystemEntity):
    """Directorio: nodo que tiene hijos."""
    children: Dict[str, FileSystemEntity] = field(default_factory=dict)

    def add_child(self, node: FileSystemEntity) -> None:
        self.children[node.name] = node
        node.parent = self

    def get_child(self, name: str) -> Optional[FileSystemEntity]:
        return self.children.get(name)

    def remove_child(self, name: str) -> Optional[FileSystemEntity]:
        return self.children.pop(name, None)
