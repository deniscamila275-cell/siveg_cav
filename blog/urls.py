"""
================================================================================
ENRUTAMIENTO DEL SISTEMA Y MAPEO DE PANTALLAS (urls.py)
================================================================================
Asocia cada dirección URL con su respectivo método controlador en views.py
para renderizar la interfaz gráfica (pantalla) correspondiente.

PANTALLA A AGREGAR (Ejemplo de registro para una nueva pantalla):
    1. Definir la función en views.py: def mi_nueva_pantalla(request): ...
    2. Agregar la ruta aquí en urlpatterns:
       path('mi-nueva-pantalla/', views.mi_nueva_pantalla, name='mi_nueva_pantalla'),
================================================================================
"""

from django.urls import path
from . import views

urlpatterns = [
    # PANTALLA 1: Portal Vecinal (Atención al ciudadano y consultas inteligentes)
    path('', views.portal_vecino, name='portal_vecino'),

    # PANTALLA 2: Mesa de Entrada (Gestión operativa y derivación de expedientes)
    path('gestion/', views.mesa_entrada, name='mesa_entrada'),

    # PANTALLA 3: Panel Gerencial / Dashboard (Monitoreo de métricas y trazabilidad)
    path('panel/', views.panel_gerencial, name='panel_gerencial'),
]
