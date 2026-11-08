#!/usr/bin/env python
"""
================================================================================
SOPORTE DEL SISTEMA: Entry Point CLI de Django (manage.py)
================================================================================
OBJETIVO DEL PROYECTO:
    Sistema Integrado de Vecinos y Gestión (SIVEG / SIGEV Posadas).
    Este archivo proporciona el soporte de ejecución en consola para:
    - Iniciar el servidor web de desarrollo: python manage.py runserver
    - Aplicar migraciones a la Base de Datos: python manage.py migrate
    - Ejecutar la suite de pruebas unitarias: python manage.py test
================================================================================
"""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sigev_project.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
