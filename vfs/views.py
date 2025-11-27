from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from .core.fs import SistemaArchivos, NotFound, PermError


def _ensure_fs(session):
    state = session.get("fs_state")
    if state:
        fs = SistemaArchivos.from_dict(state)
    else:
        fs = SistemaArchivos()
        session["fs_state"] = fs.to_dict()
        session.modified = True
    return fs


def vfs_home(request):
    fs = _ensure_fs(request.session)
    output = request.session.get("vfs_output", "")
    return render(
        request,
        "vfs/home.html",
        {
            "output": output,
            "cwd": fs.pwd(),
            "user": fs.usuario_actual.nombre,  # alias a username
        },
    )


@require_POST
def run_command(request):
    fs = _ensure_fs(request.session)
    cmdline = request.POST.get("command", "").strip()
    out = ""

    try:
        if cmdline:
            parts = cmdline.split()
            cmd, args = parts[0], parts[1:]

            if cmd == "ls":
                out = "\n".join(fs.ls(args[0] if args else None))
            elif cmd == "cd":
                if not args:
                    out = fs.cd("/")
                else:
                    out = fs.cd(args[0])
            elif cmd == "mkdir":
                out = fs.mkdir(args[0])
            elif cmd == "touch":
                out = fs.touch(args[0])
            elif cmd == "cat":
                out = fs.cat(args[0])
            elif cmd == "echo":
                nombre = args[0]
                contenido = " ".join(args[1:])
                out = fs.echo(nombre, contenido)
            elif cmd == "chmod":
                out = fs.chmod(args[0], args[1])
            elif cmd == "su":
                out = fs.su(args[0])
            elif cmd == "pwd":
                out = fs.pwd()
            elif cmd == "tree":
                ruta = args[0] if args else None
                out = fs.tree(ruta)
            elif cmd == "rm":
                if not args:
                    out = "Uso: rm [-r] RUTA"
                else:
                    recursive = False
                    ruta = None
                    if args[0] in ("-r", "-R"):
                        if len(args) < 2:
                            out = "Uso: rm [-r] RUTA"
                        else:
                            recursive = True
                            ruta = args[1]
                    else:
                        ruta = args[0]

                    if ruta:
                        out = fs.rm(ruta, recursive=recursive)
            else:
                out = f"Comando no soportado: {cmd}"
    except (NotFound, PermError, Exception) as e:
        out = f"Error: {e}"

    # Persistir salida y estado
    request.session["vfs_output"] = out
    request.session["fs_state"] = fs.to_dict()
    request.session.modified = True
    return redirect("vfs_home")
