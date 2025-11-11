from django import forms
ALGORITHMS = [
    ('fcfs', 'FCFS'),
    ('rr', 'Round Robin'),
    ('sjf', 'SJF (No expropiativo)'),
]
class ProcessForm(forms.Form):
    procesos_json = forms.CharField(
        widget=forms.Textarea(attrs={'rows':8}),
        label='Procesos (JSON)',
        initial='[\n  {"pid": 1, "llegada": 0, "rafaga": 5, "usuario": "usuario1"},\n  {"pid": 2, "llegada": 1, "rafaga": 3, "usuario": "usuario2"}\n]'
    )
    algoritmo = forms.ChoiceField(choices=ALGORITHMS, initial='fcfs', label='Algoritmo')
    quantum = forms.IntegerField(min_value=1, initial=2, required=False, label='Quantum (RR)')
