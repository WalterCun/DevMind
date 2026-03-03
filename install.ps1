# devmind-core/install.ps1

Write-Host "🚀 DevMind Core - Instalación Nativa con uv (Windows)" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

# 1. Verificar Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python detectado: $pythonVersion"
} catch {
    Write-Host "❌ Python no detectado. Instala Python 3.10+" -ForegroundColor Red
    exit 1
}

# 2. Verificar uv
try {
    $uvVersion = uv --version 2>&1
    Write-Host "✅ uv detectado: $uvVersion"
} catch {
    Write-Host "⚠️ uv no detectado. Instalando uv..." -ForegroundColor Yellow
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
}

# 3. Verificar Docker
try {
    docker ps | Out-Null
    Write-Host "✅ Docker detectado y corriendo" -ForegroundColor Green
    $dockerAvailable = $true
} catch {
    Write-Host "⚠️ Docker no detectado (sandbox limitado)" -ForegroundColor Yellow
    $dockerAvailable = $false
}

# 4. Crear directorio home
$devmindHome = if ($env:DEVMENT_HOME) { $env:DEVMENT_HOME } else { "$env:USERPROFILE\.devmind" }
New-Item -ItemType Directory -Force -Path $devmindHome | Out-Null
Write-Host "📁 Directorio home: $devmindHome"

# 5. Crear entorno virtual con uv
Write-Host "🐍 Creando entorno virtual con uv..." -ForegroundColor Cyan
uv venv "$devmindHome\venv"

# 6. Instalar dependencias
Write-Host "📦 Instalando dependencias con uv..." -ForegroundColor Cyan
& "$devmindHome\venv\Scripts\Activate.ps1"
uv pip install -e .

# 7. Descargar modelos Ollama
Write-Host "🤖 Configurando Ollama..." -ForegroundColor Cyan
ollama pull llama3 2>$null
ollama pull codellama 2>$null
ollama pull nomic-embed-text 2>$null

# 8. Crear configuración inicial
$configPath = "$devmindHome\config.json"
if (-not (Test-Path $configPath)) {
    Write-Host "📝 Creando configuración inicial..." -ForegroundColor Cyan
    $config = @{
        agent_name = "DevMind"
        personality = "professional"
        autonomy_mode = "supervised"
        sandbox_enabled = $dockerAvailable
        initialized = $false
    } | ConvertTo-Json
    $config | Out-File -FilePath $configPath -Encoding utf8
}

Write-Host ""
Write-Host "✅ ¡Instalación completada!" -ForegroundColor Green
Write-Host ""
Write-Host "Próximos pasos:"
Write-Host "  1. Activa el entorno: $devmindHome\venv\Scripts\Activate.ps1"
Write-Host "  2. Ejecuta: devmind init"
Write-Host "  3. Completa el wizard de configuración"
Write-Host "  4. Comienza a crear: devmind chat"
Write-Host ""