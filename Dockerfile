FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    git \
    docker.io \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar uv (gestor de paquetes rápido)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copiar archivos de configuración de uv
COPY pyproject.toml uv.lock ./

# Instalar dependencias con uv
RUN uv sync --frozen --no-dev

# Copiar el código fuente
COPY . .

# Instalar el paquete en modo editable
RUN uv pip install -e .

# Crear directorios necesarios para la ejecución
RUN mkdir -p /app/projects /app/addons /app/tools/auto_generated /app/.memory

# Punto de entrada
ENTRYPOINT ["devmind"]
CMD ["--help"]