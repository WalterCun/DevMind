#!/bin/bash

set -e

echo "🚀 DevMind Core - Instalación Nativa"
echo "====================================="

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3.10+ requerido"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
if (( $(echo "$PYTHON_VERSION < 3.10" | bc -l) )); then
    echo "❌ Python 3.10+ requerido (tienes $PYTHON_VERSION)"
    exit 1
fi

# Verificar Docker (opcional para sandbox)
if command -v docker &> /dev/null; then
    echo "✅ Docker detectado"
    DOCKER_AVAILABLE=true
else
    echo "⚠️ Docker no detectado (sandbox limitado)"
    DOCKER_AVAILABLE=false
fi

# Crear directorio home
DEVMENT_HOME="${DEVMENT_HOME:-$HOME/.devmind}"
mkdir -p "$DEVMENT_HOME"
echo "📁 Directorio home: $DEVMENT_HOME"

# Crear virtual environment
echo "🐍 Creando virtual environment..."
python3 -m venv "$DEVMENT_HOME/venv"
source "$DEVMENT_HOME/venv/bin/activate"

# Instalar dependencias
echo "📦 Instalando dependencias..."
pip install --upgrade pip
pip install -e .

# Descargar modelos Ollama recomendados
echo "🤖 Configurando Ollama..."
ollama pull llama3 2>/dev/null || echo "⚠️ Ollama no disponible o modelo no encontrado"
ollama pull codellama 2>/dev/null || true
ollama pull nomic-embed-text 2>/dev/null || true

# Crear archivo de configuración inicial
if [ ! -f "$DEVMENT_HOME/config.json" ]; then
    echo "📝 Creando configuración inicial..."
    cat > "$DEVMENT_HOME/config.json" << EOF
{
    "agent_name": "DevMind",
    "personality": "professional",
    "autonomy_mode": "supervised",
    "sandbox_enabled": $DOCKER_AVAILABLE,
    "initialized": false
}
EOF
fi

echo ""
echo "✅ Instalación completada!"
echo ""
echo "Próximos pasos:"
echo "  1. Ejecuta: devmind init"
echo "  2. Completa el wizard de configuración"
echo "  3. Comienza a crear: devmind chat"
echo ""