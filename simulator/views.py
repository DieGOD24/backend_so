from django.shortcuts import render
from .forms import ProcessForm
from .core.scheduler import Planificador
import json
def sim_home(request):
    form = ProcessForm()
    return render(request, 'simulator/home.html', {'form': form})
def run_simulation(request):
    form = ProcessForm(request.POST or None)
    result = None; error = None
    if request.method == 'POST' and form.is_valid():
        try:
            procesos = json.loads(form.cleaned_data['procesos_json'])
            algoritmo = form.cleaned_data['algoritmo']
            quantum = form.cleaned_data.get('quantum') or 2
            plan = Planificador()
            if algoritmo == 'fcfs':
                result = plan.fcfs(procesos)
            elif algoritmo == 'rr':
                result = plan.round_robin(procesos, quantum=int(quantum))
            elif algoritmo == 'sjf':
                result = plan.sjf(procesos)
            else:
                error = 'Algoritmo no soportado'
        except Exception as e:
            error = str(e)
    return render(request, 'simulator/home.html', {'form': form, 'result': result, 'error': error})
