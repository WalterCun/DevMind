#!/bin/bash
# devmind-core/install.sh

set -e

echo "🚀 DevMind Core - Instalación Nativa con uv"
echo "============================================"

# 1. Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3.10+ requerido"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
if (( $(echo "$PYTHON_VERSION < 3.10" | bc -l) )); then
    echo "❌ Python 3.10+ requerido (tienes $PYTHON_VERSION)"
    exit 1
fi

# 2. Verificar uv
if ! command -v uv &> /dev/null; then
    echo "⚠️ uv no detectado. Instalando uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "✅ uv detectado: $(uv --version)"

# 3. Verificar Docker (opcional para sandbox)
if command -v docker &> /dev/null && docker ps &> /dev/null; then
    echo "✅ Docker detectado y corriendo"
    DOCKER_AVAILABLE=true
else
    echo "⚠️ Docker no detectado (sandbox limitado)"
    DOCKER_AVAILABLE=false
fi

# 4. Crear directorio home
DEVMENT_HOME="${DEVMENT_HOME:-$HOME/.devmind}"
mkdir -p "$DEVMENT_HOME"
echo "📁 Directorio home: $DEVMENT_HOME"

# 5. Crear entorno virtual con uv
echo "🐍 Creando entorno virtual con uv..."
uv venv "$DEVMENT_HOME/venv"

# 6. Instalar dependencias
echo "📦 Instalando dependencias con uv..."
source "$DEVMENT_HOME/venv/bin/activate"
uv pip install -e .

# 7. Descargar modelos Ollama recomendados
echo "🤖 Configurando Ollama..."
ollama pull llama3 2>/dev/null || echo "⚠️ Ollama no disponible o modelo no encontrado"
ollama pull codellama 2>/dev/null || true
ollama pull nomic-embed-text 2>/dev/null || true

# 8. Crear archivo de configuración inicial
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
echo "✅ ¡Instalación completada!"
echo ""
echo "Próximos pasos:"
echo "  1. Activa el entorno: source $DEVMENT_HOME/venv/bin/activate"
echo "  2. Ejecuta: devmind init"
echo "  3. Completa el wizard de configuración"
echo "  4. Comienza a crear: devmind chat"
echo ""