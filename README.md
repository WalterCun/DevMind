# 🤖 DevMind Core

**Tu ingeniero de software autónomo, ejecutándose 100% en tu máquina.**

DevMind Core es una plataforma de desarrollo auto-alojada que actúa como un equipo de ingeniería completo. Planifica, codifica, depura y se auto-mejora mediante conversación natural, sin depender de la nube.

## ✨ Características Principales

- 🏠 **100% Local**: Privacidad total, cero datos salen de tu máquina
- 🧠 **Memoria Persistente**: Recuerda decisiones, código y contexto entre sesiones
- 🛡️ **Seguridad Híbrida**: Modos supervisado y autónomo con sandbox Docker
- 🔄 **Auto-Mejora**: Crea sus propias herramientas y aprende nuevos lenguajes
- 🏢 **Jerarquía de Agentes**: 12+ agentes especializados (Director, Arquitecto, Dev, QA, etc.)

## 🚀 Instalación Rápida

### Opción A: Docker (Recomendado)
```bash
git clone https://github.com/tu/devmind-core.git
cd devmind-core
cp .env.example .env
docker-compose --profile full up -d
docker-compose exec app devmind init
```
### Opción B: Nativo con uv
```bash
git clone https://github.com/tu/devmind-core.git
cd devmind-core
curl -LsSf https://astral.sh/uv/install.sh | sh
./install.sh  # Linux/Mac
# o
.\install.ps1  # Windows
devmind init
```

📚 Documentación
Instalación
Configuración
Agentes
Seguridad

🛠️ Stack Tecnológico
- Lenguaje: Python 3.10+
- Framework: Django + Django-Ninja
- Agentes: CrewAI + LangChain
- LLM Local: Ollama (Llama3, Codellama)
- Memoria: PostgreSQL + ChromaDB
- Sandbox: Docker
- Package Manager: uv

📄 Licencia
MIT License - Ver LICENSE para más detalles.

```markdown

### `# devmind-core/LICENSE`
```text
MIT License

Copyright (c) 2024 DevMind Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
5. Instrucciones para Iniciar

Para validar que la Fase 0 - Sprint 0.1 está completa, ejecuta lo siguiente en tu terminal:
1. Crea la estructura y archivos:
Copia el contenido anterior en sus respectivos archivos dentro de la carpeta devmind-core.

2. Prepara el entorno (Nativo):

```bash
cd devmind-core
chmod +x install.sh
./install.sh
```
3. O prepara el entorno (Docker):

```
cd devmind-core
cp .env.example .env
docker-compose --profile full up -d
```

4. Verifica la instalación:
```
# Si es nativo (asegúrate de activar el venv primero)
source ~/.devmind/venv/bin/activate
devmind --version

# Si es Docker
docker-compose exec app devmind --version
```
