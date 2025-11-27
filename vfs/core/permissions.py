from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Set


class Permission(str, Enum):
    """Banderas de permisos rwx soportadas."""
    READ = "r"
    WRITE = "w"
    EXECUTE = "x"


@dataclass
class PermissionSet:
    """
    Conjunto de permisos tipo Unix simplificado (solo propietario).
    """
    owner: Set[Permission] = field(default_factory=set)

    @classmethod
    def from_string(cls, spec: str) -> "PermissionSet":
        """
        Parsea cadenas como 'rw', 'rwx'. 
        Ignora caracteres que no sean r/w/x.
        """
        return cls(owner={Permission(ch) for ch in spec if ch in {"r", "w", "x"}})

    def allows(self, permission: Permission) -> bool:
        """True si el permiso solicitado está concedido al propietario."""
        return permission in self.owner

    def to_string(self) -> str:
        """Serializa a string ('rw', 'rwx' o '-' si no hay permisos)."""
        granted = "".join(p.value for p in sorted(self.owner, key=str))
        return granted or "-"
