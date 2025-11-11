from .inodes import Archivo, Directorio
from .users import DEFAULT_USERS

class PermError(Exception):
    ...

class NotFound(Exception):
    ...

class SistemaArchivos:
    """
    Sistema de archivos virtual con serialización a dict (JSON-safe).
    Guarda solo estado serializable en sesión y soporta cd .. (normalización).
    """
    def __init__(self):
        # Usuarios base
        self.usuarios = DEFAULT_USERS.copy()

        # Árbol base: / y /home/{usuario1,usuario2}
        self.raiz = Directorio('/', self.usuarios['root'], permisos='rwxr-xr-x')
        self.cwd = self.raiz
        self.cwd_path = '/'
        self.usuario_actual = self.usuarios['root']

        home = Directorio('home', self.usuarios['root'], permisos='rwxr-xr-x')
        self.raiz.add(home)
        for u in ['usuario1', 'usuario2']:
            d = Directorio(u, self.usuarios[u], permisos='rwxr-x---')
            home.add(d)

    # -------------------------
    # Normalización de rutas
    # -------------------------
    def _normalize_path(self, ruta: str) -> str:
        """
        Devuelve una ruta absoluta normalizada, resolviendo '.' y '..'
        respecto al cwd actual si la ruta es relativa.
        """
        if not ruta:
            return self.cwd_path

        # Base: cwd si es relativa; raíz si es absoluta
        base_parts = [] if ruta.startswith('/') else [p for p in self.cwd_path.split('/') if p]
        for token in [p for p in ruta.split('/') if p]:
            if token == '.':
                continue
            elif token == '..':
                if base_parts:
                    base_parts.pop()
            else:
                base_parts.append(token)
        return '/' + '/'.join(base_parts)

    # -------------------------
    # Resolución de rutas
    # -------------------------
    def _split_path(self, ruta: str):
        abs_path = self._normalize_path(ruta)
        parts = [p for p in abs_path.split('/') if p]
        base = self.raiz
        return base, parts

    def _resolve(self, ruta: str):
        base, parts = self._split_path(ruta)
        cur = base
        for p in parts:
            if not isinstance(cur, Directorio):
                raise NotFound("No es un directorio")
            nxt = cur.get(p)
            if not nxt:
                raise NotFound(f"No existe: {p}")
            cur = nxt
        return cur

    # -------------------------
    # Permisos (muy simplificados)
    # -------------------------
    def _check_read(self, nodo):
        if self.usuario_actual.nombre == 'root':
            return True
        # Lectura si es propietario o grupo/otros con 'r'
        return (
            'r' in nodo.permisos[3:6] or
            'r' in nodo.permisos[6:9] or
            nodo.propietario == self.usuario_actual
        )

    def _check_write(self, nodo):
        if self.usuario_actual.nombre == 'root':
            return True
        # Escritura si es propietario o grupo con 'w'
        return (
            'w' in nodo.permisos[3:6] or
            nodo.propietario == self.usuario_actual
        )

    # -------------------------
    # Operaciones tipo shell
    # -------------------------
    def ls(self, ruta: str = None):
        target = self.cwd if ruta is None else self._resolve(ruta if ruta else self.cwd_path)
        if not isinstance(target, Directorio):
            raise NotFound("No es un directorio")
        if not self._check_read(target):
            raise PermError("Permiso denegado")
        return sorted(target.hijos.keys())

    def cd(self, ruta: str):
        path = self._normalize_path(ruta)
        target = self._resolve(path)
        if not isinstance(target, Directorio):
            raise NotFound("No es un directorio")
        if not self._check_read(target):
            raise PermError("Permiso denegado")
        self.cwd = target
        self.cwd_path = path
        return self.cwd_path

    def mkdir(self, nombre: str):
        if not self._check_write(self.cwd):
            raise PermError("Permiso denegado")
        if nombre in self.cwd.hijos:
            raise Exception("Ya existe")
        d = Directorio(nombre, self.usuario_actual, permisos='rwxr-x---')
        self.cwd.add(d)
        return f"Directorio {nombre} creado"

    def touch(self, nombre: str):
        if not self._check_write(self.cwd):
            raise PermError("Permiso denegado")
        if nombre in self.cwd.hijos:
            return "Actualizado timestamp (simulado)"
        f = Archivo(nombre, self.usuario_actual, permisos='rw-r-----')
        self.cwd.add(f)
        return f"Archivo {nombre} creado"

    def cat(self, nombre: str):
        nodo = self.cwd.get(nombre)
        if not nodo or not isinstance(nodo, Archivo):
            raise NotFound("Archivo no encontrado")
        if not self._check_read(nodo):
            raise PermError("Permiso denegado")
        return nodo.contenido

    def echo(self, nombre: str, contenido: str):
        nodo = self.cwd.get(nombre)
        if not nodo or not isinstance(nodo, Archivo):
            raise NotFound("Archivo no encontrado")
        if not self._check_write(nodo):
            raise PermError("Permiso denegado")
        nodo.contenido = contenido
        nodo.tamanio = len(contenido.encode('utf-8'))
        return f"{len(contenido)} bytes escritos"

    def chmod(self, nombre: str, permisos: str):
        nodo = self.cwd.get(nombre)
        if not nodo:
            raise NotFound("No existe")
        if self.usuario_actual.nombre != 'root' and nodo.propietario != self.usuario_actual:
            raise PermError("Solo propietario o root puede cambiar permisos")
        if len(permisos) != 9:
            raise Exception("Formato: 'rwxrwxrwx'")
        nodo.permisos = permisos
        return f"Permisos de {nombre} -> {permisos}"

    def su(self, usuario: str):
        if usuario not in self.usuarios:
            raise NotFound("Usuario no existe")
        self.usuario_actual = self.usuarios[usuario]
        return f"Cambiado a {usuario}"

    def pwd(self):
        return self.cwd_path

    # -------------------------
    # Serialización JSON-safe
    # -------------------------
    def to_dict(self):
        """Convierte todo el estado del FS a un dict JSON-serializable."""
        return {
            "cwd_path": self.cwd_path,
            "usuario": self.usuario_actual.nombre,
            "arbol": self._serialize_node(self.raiz),
        }

    @staticmethod
    def from_dict(data):
        """Reconstruye el FS a partir del dict; cae a estado limpio ante error."""
        fs = SistemaArchivos()
        if not data:
            return fs
        try:
            # Restaurar usuario actual
            nombre_usuario = data.get("usuario", "root")
            fs.usuario_actual = fs.usuarios.get(nombre_usuario, fs.usuarios["root"])
            # Restaurar árbol
            fs.raiz = fs._deserialize_node(data.get("arbol"))
            # Restaurar cwd
            fs.cwd_path = data.get("cwd_path", "/")
            fs.cwd = fs._resolve(fs.cwd_path)
        except Exception:
            fs = SistemaArchivos()
        return fs

    def _serialize_node(self, nodo):
        """Serializa recursivamente Directorio/Archivo."""
        base = {
            "tipo": "dir" if hasattr(nodo, "hijos") else "file",
            "nombre": nodo.nombre,
            "propietario": nodo.propietario.nombre,
            "permisos": nodo.permisos,
        }
        if base["tipo"] == "dir":
            base["hijos"] = [self._serialize_node(h) for h in nodo.hijos.values()]
        else:
            base["contenido"] = nodo.contenido
            base["tamanio"] = nodo.tamanio
        return base

    def _deserialize_node(self, data):
        """Desserializa recursivamente a Directorio/Archivo."""
        if not data:
            return self.raiz
        owner = self.usuarios.get(data["propietario"], self.usuarios["root"])
        if data["tipo"] == "dir":
            d = Directorio(data["nombre"], owner, permisos=data["permisos"])
            for hijo in data.get("hijos", []):
                n = self._deserialize_node(hijo)
                d.add(n)
            return d
        else:
            f = Archivo(data["nombre"], owner, permisos=data["permisos"])
            f.contenido = data.get("contenido", "")
            f.tamanio = data.get("tamanio", 0)
            return f
