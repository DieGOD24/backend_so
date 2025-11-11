# Usa una imagen base ligera de Python
FROM python:3.12.7-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia el requirements.txt e instala dependencias
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Instala dependencias del sistema necesarias para PostgreSQL y zona horaria
RUN apt-get update && apt-get install -y \
    libpq-dev \
    tzdata \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copia el resto de los archivos de la app
COPY . .

# Copia el entrypoint y le da permisos
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Define el script de entrada por defecto
ENTRYPOINT ["/entrypoint.sh"]

# Comando por defecto (se puede sobrescribir en docker-compose o CLI)
# Editar por aplicacion principal con WSGI con gunicorn
# Editar por aplicacion principal con ASGI con uvicorn
CMD ["gunicorn", "os_simulator.wsgi:application", "--bind", "0.0.0.0:8000"]
