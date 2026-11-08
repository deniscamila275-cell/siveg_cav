# Sistema Integral de Asesoramiento y Atención al Vecino (SIVEG)

Proyecto de desarrollo para el 2do año de la carrera Analista en Sistemas - ISVD Posadas.

## Requisitos Previos
El sistema utiliza **SQLite** como base de datos por defecto, por lo que no requiere configuraciones externas de motor de datos.

## Cómo ejecutar el proyecto en tu computadora:

1. **Clonar o descargar el repositorio:**
   ```bash
   git clone https://github.com
   ```

2. **Instalar las dependencias:**
   Asegúrate de tener Python instalado y ejecuta:
   ```bash
   pip install -r requirements.txt
   ```

3. **Realizar las migraciones de la base de datos (SQLite):**
   ```bash
   python manage.py migrate
   ```

4. **Iniciar el servidor de desarrollo:**
   ```bash
   python manage.py runserver
   ```
   Luego, abre en tu navegador: `http://127.0.0`
