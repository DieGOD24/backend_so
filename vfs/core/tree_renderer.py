from __future__ import annotations

from .models import Directory


def render_tree(root: Directory) -> str:
    """
    Devuelve una representación legible del árbol de directorios, tipo `tree`.
    Directorios terminan en '/', archivos no.
    """
    lines: list[str] = []

    def _render(dir_node: Directory, prefix: str = ""):
        # Primero directorios, luego archivos (ordenados alfabéticamente)
        children = sorted(
            dir_node.children.values(),
            key=lambda node: (0 if isinstance(node, Directory) else 1, node.name.lower()),
        )

        for i, child in enumerate(children):
            is_last = (i == len(children) - 1)
            connector = "└── " if is_last else "├── "

            if isinstance(child, Directory):
                lines.append(f"{prefix}{connector}{child.name}/")
                extension = "    " if is_last else "│   "
                _render(child, prefix + extension)
            else:
                lines.append(f"{prefix}{connector}{child.name}")

    root_name = root.name or "/"
    lines.append(f"{root_name}/")
    _render(root, "")

    return "\n".join(lines)
