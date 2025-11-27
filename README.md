# Sistema Integrado: Planificación de Procesos y Gestión de Archivos

# Elaborado por:
- Maicol Stiven - stiven.ruiz@utp.edu.co
- Kevin Esguerra - kevin.esguerra@utp.edu.co
- Isabella Cardona - i.cardona1@utp.edu.co
- Diego Giraldo - diego.giraldo2@utp.edu.co


## Requisitos
- Python 3.12
- Django

## Instalación
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install Django
python manage.py migrate
python manage.py runserver
```
- Planificador: http://127.0.0.1:8000/sim/
- VFS: http://127.0.0.1:8000/vfs/

## Macroalgoritmos
- FCFS: ordenar por llegada, ejecutar completo, sin interrupciones.
- RR: cola circular, quantum, reinsertar si resta CPU.
- SJF: elegir ráfaga más corta (no expropiativo).
