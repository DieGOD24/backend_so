from django.urls import path
from . import views
urlpatterns = [
    path('', views.vfs_home, name='vfs_home'),
    path('cmd/', views.run_command, name='vfs_cmd'),
]
