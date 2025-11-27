from __future__ import annotations

from dataclasses import dataclass

from .models import Directory, File, FileSystemEntity, User
from .permissions import Permission, PermissionSet
from .tree_renderer import render_tree


@dataclass
class FileSystemOps:
    """
    Operaciones tipo POSIX sobre el árbol (ls, cd, mkdir, touch, cat, write, rm, resolve, pwd, tree).
    Trabaja siempre con un usuario actual (self.user) y cwd (self.cwd).
    """

    root: Directory
    user: User
    cwd: Directory | None = None

    def __post_init__(self):
        if self.cwd is None:
            self.cwd = self.root

    # ------------------------- ls -------------------------
    def ls(self, path: str | None = None) -> list[str]:
        target_dir = self.cwd if path is None else self.resolve(path)

        if not isinstance(target_dir, Directory):
            raise ValueError(f"'{path or '.'}' is not a directory")

        if not self._can_read(target_dir):
            raise PermissionError(
                f"Permission denied: cannot read directory '{target_dir.name or '/'}'"
            )

        result: list[str] = []
        for name, entity in sorted(target_dir.children.items()):
            if isinstance(entity, Directory):
                result.append(f"{name}/")
            else:
                result.append(name)
        return result

    # ------------------------- cd -------------------------
    def cd(self, path: str) -> str:
        if not path:
            self.cwd = self.root
            return "/"

        target = self.resolve(path)

        if not isinstance(target, Directory):
            raise ValueError(f"'{path}' is not a directory")

        if not self._can_execute(target):
            raise PermissionError(f"Permission denied: cannot access directory '{path}'")

        self.cwd = target
        return target.path()

    # ------------------------- mkdir -------------------------
    def mkdir(self, path: str) -> Directory:
        if not path:
            raise ValueError("mkdir: missing directory name")

        parent_path, name = self._split_path(path)
        parent = (
            self.cwd
            if parent_path == "."
            else self.root if parent_path == "/" else self.resolve(parent_path)
        )

        if not isinstance(parent, Directory):
            raise ValueError(f"'{parent_path}' is not a directory")

        if not self._can_write(parent):
            raise PermissionError(
                f"Permission denied: cannot create directory in '{parent_path}'"
            )

        if parent.get_child(name):
            raise FileExistsError(f"Directory '{name}' already exists")

        new_dir = Directory(
            name=name,
            owner=self.user,
            permissions=PermissionSet.from_string("rwx"),
        )
        parent.add_child(new_dir)
        return new_dir

    # ------------------------- touch -------------------------
    def touch(self, path: str) -> File:
        if not path:
            raise ValueError("touch: missing file name")

        parent_path, name = self._split_path(path)
        parent = (
            self.cwd
            if parent_path == "."
            else self.root if parent_path == "/" else self.resolve(parent_path)
        )

        if not isinstance(parent, Directory):
            raise ValueError(f"'{parent_path}' is not a directory")

        existing = parent.get_child(name)
        if existing:
            if isinstance(existing, File):
                # En un sistema real actualizaríamos timestamps
                return existing
            else:
                raise ValueError(f"'{name}' is a directory")

        if not self._can_write(parent):
            raise PermissionError(
                f"Permission denied: cannot create file in '{parent_path}'"
            )

        new_file = File(
            name=name,
            owner=self.user,
            permissions=PermissionSet.from_string("rw"),
            content="",
        )
        parent.add_child(new_file)
        return new_file

    # ------------------------- cat -------------------------
    def cat(self, path: str) -> str:
        if not path:
            raise ValueError("cat: missing file name")

        target = self.resolve(path)

        if not isinstance(target, File):
            if isinstance(target, Directory):
                raise ValueError(f"cat: '{path}' is a directory")
            else:
                raise FileNotFoundError(f"cat: '{path}' no such file")

        if not self._can_read(target):
            raise PermissionError(f"Permission denied: cannot read file '{path}'")

        return target.content

    # ------------------------- write -------------------------
    def write(self, path: str, content: str, *, append: bool = False) -> File:
        if not path:
            raise ValueError("write: missing file name")

        parent_path, name = self._split_path(path)
        parent = (
            self.cwd
            if parent_path == "."
            else self.root if parent_path == "/" else self.resolve(parent_path)
        )

        if not isinstance(parent, Directory):
            raise ValueError(f"'{parent_path}' is not a directory")

        existing = parent.get_child(name)

        if existing:
            if not isinstance(existing, File):
                raise ValueError(f"'{name}' is a directory")

            if not self._can_write(existing):
                raise PermissionError(
                    f"Permission denied: cannot write to file '{path}'"
                )

            if append:
                existing.content += content
            else:
                existing.content = content
            return existing
        else:
            if not self._can_write(parent):
                raise PermissionError(
                    f"Permission denied: cannot create file in '{parent_path}'"
                )

            new_file = File(
                name=name,
                owner=self.user,
                permissions=PermissionSet.from_string("rw"),
                content=content,
            )
            parent.add_child(new_file)
            return new_file

    # ------------------------- rm -------------------------
    def rm(self, path: str, *, recursive: bool = False) -> None:
        if not path:
            raise ValueError("rm: missing file or directory name")

        target = self.resolve(path)
        parent = target.parent

        if parent is None:
            raise ValueError("rm: cannot remove root directory")

        if not self._can_write(parent):
            raise PermissionError(f"Permission denied: cannot remove '{path}'")

        if isinstance(target, Directory) and target.children and not recursive:
            raise ValueError(
                f"rm: cannot remove '{path}': Directory not empty (use recursive flag)"
            )

        parent.remove_child(target.name)

    # ------------------------- resolve -------------------------
    def resolve(self, path: str) -> FileSystemEntity:
        if not path or path == ".":
            return self.cwd

        if path == "/":
            return self.root

        if path == "..":
            return self.cwd.parent if self.cwd.parent else self.root

        if path.startswith("/"):
            current: FileSystemEntity = self.root
            path_parts = [p for p in path.split("/") if p]
        else:
            current = self.cwd
            path_parts = [p for p in path.split("/") if p]

        for part in path_parts:
            if part == ".":
                continue
            elif part == "..":
                current = current.parent if current.parent else self.root
            else:
                if not isinstance(current, Directory):
                    raise FileNotFoundError(
                        f"'{part}' not found: parent is not a directory"
                    )

                child = current.get_child(part)
                if child is None:
                    raise FileNotFoundError(f"'{part}' not found")
                current = child

        return current

    # ------------------------- otros helpers -------------------------
    def pwd(self) -> str:
        return self.cwd.path()

    def tree(self, path: str | None = None) -> str:
        target = self.cwd if path is None else self.resolve(path)
        if not isinstance(target, Directory):
            raise ValueError(f"'{path or '.'}' is not a directory")
        return render_tree(target)

    def _split_path(self, path: str) -> tuple[str, str]:
        if "/" in path:
            parent, name = path.rsplit("/", 1)
            return parent if parent else "/", name
        else:
            return ".", path

    def _can_read(self, entity: FileSystemEntity) -> bool:
        if self.user.username == "root":
            return True
        return entity.owner == self.user and entity.permissions.allows(Permission.READ)

    def _can_write(self, entity: FileSystemEntity) -> bool:
        if self.user.username == "root":
            return True
        return entity.owner == self.user and entity.permissions.allows(Permission.WRITE)

    def _can_execute(self, entity: FileSystemEntity) -> bool:
        if self.user.username == "root":
            return True
        return entity.owner == self.user and entity.permissions.allows(
            Permission.EXECUTE
        )
