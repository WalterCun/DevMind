from setuptools import setup, find_packages

setup(
    name="devmind-core",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        # Core
        "django>=6.0.2",
        "django-ninja>=1.5.3",
        "crewai>=1.9.3",
        "crewai-tools>=1.9.3",
        # LLM Local
        "langchain>=1.2.10",
        "langchain-community>=0.4.1",
        "langchain-ollama>=1.0.1",
        # Memoria Vectorial
        "chromadb>=1.1.1",
        "sentence-transformers>=5.2.3",
        # Base de Datos
        "sqlalchemy>=2.0.48",
        "psycopg2-binary>=2.9.11",
        # CLI
        "click>=8.1.8",
        "rich>=14.3.3",
        "textual>=8.0.1",
        "questionary>=2.1.1",
        # Sandbox y Seguridad
        "docker>=7.1.0",
        "paramiko>=4.0.0",
        # Utilidades
        "aiohttp>=3.13.3",
        "pydantic>=2.11.10",
        "python-dotenv>=1.1.1",
        "pyyaml>=6.0.3",
    ],
    entry_points={
        "console_scripts": [
            "devmind=cli.main:main",
        ],
    },
    python_requires=">=3.10",
)