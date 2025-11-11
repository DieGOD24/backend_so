from django.urls import path
from . import views
urlpatterns = [
    path('', views.sim_home, name='sim_home'),
    path('run/', views.run_simulation, name='run_simulation'),
]
