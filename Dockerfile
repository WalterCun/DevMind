FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    git \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Instalar en modo editable
RUN pip install -e .

# Crear directorios necesarios
RUN mkdir -p /app/projects /app/addons /app/tools /app/.memory

# Entry point
ENTRYPOINT ["devmind"]
CMD ["--help"]