# Usar imagen base de Python slim para reducir tamaño
FROM python:3.11-slim

# Establecer variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production

# Crear usuario no-root para seguridad
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar requirements primero para aprovechar cache de Docker
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Crear directorios necesarios
RUN mkdir -p /app/mangas /app/data && \
    chown -R appuser:appuser /app

# Cambiar a usuario no-root
USER appuser

# Crear base de datos y configuración inicial
RUN python -c "import app; app.init_db(); app.init_default_settings()" || echo "Database initialization will happen at runtime"

# Exponer puerto
EXPOSE 5000

# Comando de salud para Docker
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/login || exit 1

# Comando por defecto
CMD ["python", "app.py"]