from django.urls import path
from . import views

app_name = 'inicio'

urlpatterns = [
    path('', views.index, name='index'),
    path('empleados/', views.empleado_list, name='empleado_list'),
    path('empleados/nuevo/', views.empleado_create, name='empleado_create'),
    path('empleados/<int:pk>/editar/', views.empleado_edit, name='empleado_edit'),
    path('empleados/<int:pk>/eliminar/', views.empleado_delete, name='empleado_delete'),
    path('licencias/', views.licencia_list, name='licencia_list'),
    path('vacaciones/', views.vacacion_list, name='vacacion_list'),
    path('vacaciones/<int:pk>/<str:accion>/', views.vacacion_decidir, name='vacacion_decidir'),
    path('documentos/', views.documento, name='documento'),
]
