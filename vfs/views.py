from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from .core.fs import SistemaArchivos, NotFound, PermError

# Guardamos en sesión solo el dict JSON-safe bajo la clave 'fs_state'
def _ensure_fs(session):
    state = session.get('fs_state')
    if state:
        fs = SistemaArchivos.from_dict(state)
    else:
        fs = SistemaArchivos()
        session['fs_state'] = fs.to_dict()
        session.modified = True
    return fs

def vfs_home(request):
    fs = _ensure_fs(request.session)
    output = request.session.get(
        'vfs_output',
        'Bienvenido. Use comandos: ls, cd, mkdir, touch, cat, echo, chmod, su, pwd'
    )
    return render(
        request,
        'vfs/home.html',
        {'output': output, 'cwd': fs.pwd(), 'user': fs.usuario_actual.nombre}
    )

@require_POST
def run_command(request):
    fs = _ensure_fs(request.session)
    cmdline = request.POST.get('command', '').strip()
    out = ""
    try:
        if cmdline:
            parts = cmdline.split()
            cmd, args = parts[0], parts[1:]
            if cmd == 'ls':
                out = "\n".join(fs.ls(args[0] if args else None))
            elif cmd == 'cd':
                out = fs.cd(args[0])
            elif cmd == 'mkdir':
                out = fs.mkdir(args[0])
            elif cmd == 'touch':
                out = fs.touch(args[0])
            elif cmd == 'cat':
                out = fs.cat(args[0])
            elif cmd == 'echo':
                nombre = args[0]
                contenido = " ".join(args[1:])
                out = fs.echo(nombre, contenido)
            elif cmd == 'chmod':
                out = fs.chmod(args[0], args[1])
            elif cmd == 'su':
                out = fs.su(args[0])
            elif cmd == 'pwd':
                out = fs.pwd()
            else:
                out = f"Comando no soportado: {cmd}"
    except (NotFound, PermError, Exception) as e:
        out = f"Error: {e}"

    # Persistir salida y estado serializado
    request.session['vfs_output'] = out
    request.session['fs_state'] = fs.to_dict()
    request.session.modified = True
    return redirect('vfs_home')
