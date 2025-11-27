from __future__ import annotations

from typing import Dict, Any, Optional

from .models import Directory, File, User, FileSystemEntity
from .permissions import PermissionSet
from .ops import FileSystemOps
from .tree_renderer import render_tree


class PermError(Exception):
    ...


class NotFound(Exception):
    ...


class SistemaArchivos:
    """
    Envoltorio de alto nivel alrededor de FileSystemOps, con:
    - Usuarios múltiples (root, usuario1, usuario2)
    - Serialización JSON-safe para usar en sesión de Django.
    - API compatible con tu vista: ls, cd, mkdir, touch, cat, echo, chmod, su, pwd, tree, rm.
    """

    def __init__(self):
        # Usuarios base
        self.usuarios: Dict[str, User] = {
            "root": User(username="root", home="/"),
            "usuario1": User(username="usuario1", home="/home/usuario1"),
            "usuario2": User(username="usuario2", home="/home/usuario2"),
        }

        # Directorio raíz
        root_perms = PermissionSet.from_string("rwx")
        self.root = Directory(name="", owner=self.usuarios["root"], permissions=root_perms)

        # /home y /home/{usuario1,usuario2}
        home_dir = Directory(name="home", owner=self.usuarios["root"], permissions=root_perms)
        self.root.add_child(home_dir)

        for uname in ("usuario1", "usuario2"):
            user_dir = Directory(
                name=uname,
                owner=self.usuarios[uname],
                permissions=PermissionSet.from_string("rwx"),
            )
            home_dir.add_child(user_dir)

        # Usuario actual y operaciones
        self.usuario_actual: User = self.usuarios["root"]
        self.ops = FileSystemOps(root=self.root, user=self.usuario_actual)

    # ------------ API usada por las vistas ------------

    def ls(self, ruta: Optional[str] = None) -> list[str]:
        try:
            return self.ops.ls(ruta)
        except PermissionError as e:
            raise PermError(str(e))
        except FileNotFoundError as e:
            raise NotFound(str(e))
        except ValueError as e:
            raise Exception(str(e))

    def cd(self, ruta: str) -> str:
        try:
            return self.ops.cd(ruta)
        except PermissionError as e:
            raise PermError(str(e))
        except FileNotFoundError as e:
            raise NotFound(str(e))
        except ValueError as e:
            raise Exception(str(e))

    def mkdir(self, ruta: str) -> str:
        try:
            nuevo = self.ops.mkdir(ruta)
            return f"Directorio {nuevo.path()} creado"
        except PermissionError as e:
            raise PermError(str(e))
        except FileExistsError as e:
            raise Exception(str(e))
        except FileNotFoundError as e:
            raise NotFound(str(e))
        except ValueError as e:
            raise Exception(str(e))

    def touch(self, ruta: str) -> str:
        try:
            f = self.ops.touch(ruta)
            return f"Archivo {f.path()} creado/actualizado"
        except PermissionError as e:
            raise PermError(str(e))
        except FileNotFoundError as e:
            raise NotFound(str(e))
        except ValueError as e:
            raise Exception(str(e))

    def cat(self, ruta: str) -> str:
        try:
            return self.ops.cat(ruta)
        except PermissionError as e:
            raise PermError(str(e))
        except FileNotFoundError as e:
            raise NotFound(str(e))
        except ValueError as e:
            raise Exception(str(e))

    def echo(self, ruta: str, contenido: str) -> str:
        try:
            self.ops.write(ruta, contenido, append=False)
            return f"{len(contenido)} bytes escritos"
        except PermissionError as e:
            raise PermError(str(e))
        except FileNotFoundError as e:
            raise NotFound(str(e))
        except ValueError as e:
            raise Exception(str(e))

    def rm(self, ruta: str, recursive: bool = False) -> str:
        try:
            self.ops.rm(ruta, recursive=recursive)
            return f"{ruta} eliminado"
        except PermissionError as e:
            raise PermError(str(e))
        except FileNotFoundError as e:
            raise NotFound(str(e))
        except ValueError as e:
            raise Exception(str(e))

    def chmod(self, ruta: str, permisos: str) -> str:
        """
        Cambia permisos (solo propietario o root).
        Se usa solo el bloque rwx del propietario.
        """
        try:
            nodo = self.ops.resolve(ruta)
        except FileNotFoundError as e:
            raise NotFound(str(e))

        if self.usuario_actual.username != "root" and nodo.owner != self.usuario_actual:
            raise PermError("Solo propietario o root puede cambiar permisos")

        # Aceptamos 'rwxrwxrwx' pero solo usamos los primeros 3 caracteres.
        spec = permisos[:3] if len(permisos) >= 3 else permisos
        nodo.permissions = PermissionSet.from_string(spec)
        return f"Permisos de {ruta} -> {nodo.permissions.to_string()}"

    def su(self, usuario: str) -> str:
        if usuario not in self.usuarios:
            raise NotFound("Usuario no existe")

        self.usuario_actual = self.usuarios[usuario]
        self.ops.user = self.usuario_actual

        # Intentar moverse al home del usuario (si existe)
        try:
            self.ops.cd(self.usuario_actual.home)
        except Exception:
            pass

        return f"Cambiado a {usuario}"

    def pwd(self) -> str:
        return self.ops.pwd()

    def tree(self, ruta: Optional[str] = None) -> str:
        """Renderiza el árbol completo o el subárbol a partir de ruta."""
        try:
            if ruta:
                target = self.ops.resolve(ruta)
                if not isinstance(target, Directory):
                    raise NotFound(f"'{ruta}' no es un directorio")
                return render_tree(target)
            else:
                return render_tree(self.root)
        except FileNotFoundError as e:
            raise NotFound(str(e))
        except ValueError as e:
            raise Exception(str(e))

    # ------------ Serialización JSON-safe para sesión ------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "users": {name: {"home": user.home} for name, user in self.usuarios.items()},
            "current_user": self.usuario_actual.username,
            "cwd_path": self.ops.pwd(),
            "tree": self._serialize_node(self.root),
        }

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]):
        fs = cls()
        if not data:
            return fs

        try:
            # Usuarios
            users_data = data.get("users", {})
            if users_data:
                fs.usuarios = {}
                for uname, uinfo in users_data.items():
                    fs.usuarios[uname] = User(
                        username=uname,
                        home=uinfo.get("home", "/"),
                    )

            # Árbol
            tree_data = data.get("tree")
            if tree_data:
                fs.root = fs._deserialize_node(tree_data, fs.usuarios)

            # Usuario actual
            current = data.get("current_user", "root")
            fs.usuario_actual = fs.usuarios.get(current, fs.usuarios.get("root"))

            # Reconstruir ops
            fs.ops = FileSystemOps(root=fs.root, user=fs.usuario_actual)

            # cwd
            cwd_path = data.get("cwd_path", "/")
            try:
                fs.ops.cd(cwd_path)
            except Exception:
                pass
        except Exception:
            # Si algo falla, volvemos a estado limpio
            fs = cls()

        return fs

    def _serialize_node(self, nodo: FileSystemEntity) -> Dict[str, Any]:
        base: Dict[str, Any] = {
            "tipo": "dir" if isinstance(nodo, Directory) else "file",
            "nombre": nodo.name,
            "owner": nodo.owner.username,
            "permisos": nodo.permissions.to_string(),
        }
        if isinstance(nodo, Directory):
            base["hijos"] = [
                self._serialize_node(child) for child in nodo.children.values()
            ]
        else:
            base["contenido"] = nodo.content
        return base

    def _deserialize_node(self, data: Dict[str, Any], users: Dict[str, User]) -> FileSystemEntity:
        owner_name = data.get("owner", "root")
        owner = users.get(owner_name, users.get("root"))
        permisos = PermissionSet.from_string(data.get("permisos", ""))

        if data.get("tipo") == "dir":
            d = Directory(
                name=data.get("nombre", ""),
                owner=owner,
                permissions=permisos,
            )
            for hijo_data in data.get("hijos", []):
                child = self._deserialize_node(hijo_data, users)
                d.add_child(child)
            return d
        else:
            f = File(
                name=data.get("nombre", ""),
                owner=owner,
                permissions=permisos,
                content=data.get("contenido", ""),
            )
            return f
