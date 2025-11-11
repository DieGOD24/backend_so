# Sistema Integrado: Planificación de Procesos y Gestión de Archivos

## Requisitos
- Python 3.12

## Instalación
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install "Django"
python manage.py migrate
python manage.py runserver
```
- Planificador: http://127.0.0.1:8000/sim/
- VFS: http://127.0.0.1:8000/vfs/

## Macroalgoritmos
- FCFS: ordenar por llegada, ejecutar completo, sin interrupciones.
- RR: cola circular, quantum, reinsertar si resta CPU.
- SJF: elegir ráfaga más corta (no expropiativo).
