# devmind-core/db/settings.py
"""
Configuración mínima de Django para DevMind Core.

Esta configuración está optimizada para:
- Uso en CLI y scripts (no web server)
- Testing sin servidor HTTP
- Integración con PostgreSQL local/Docker
"""

from pathlib import Path
import os
import sys

# ===========================================
# RUTAS Y DIRECTORIOS
# ===========================================
BASE_DIR = Path(__file__).resolve().parent.parent

# ===========================================
# SECURITY (Desarrollo/Local)
# ===========================================
SECRET_KEY = os.getenv(
    'DJANGO_SECRET_KEY',
    'devmind-dev-secret-key-change-in-production-xyz123'
)

DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv(
    'DJANGO_ALLOWED_HOSTS',
    'localhost,127.0.0.1,[::1]'
).split(',')

# ===========================================
# APLICACIONES INSTALADAS
# ===========================================
INSTALLED_APPS = [
    # Django core
    'django.contrib.contenttypes',  # Requerido para GenericForeignKeys

    # Nuestras apps
    'db',  # Modelos de DevMind
]

# ===========================================
# MIDDLEWARE (Mínimo para CLI)
# ===========================================
MIDDLEWARE = [
    # Sin middleware web - solo ORM
]

# ===========================================
# URLCONF Y ROOT
# ===========================================
ROOT_URLCONF = None  # No usamos URLs en modo CLI

# ===========================================
# BASE DE DATOS
# ===========================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'devmind'),
        'USER': os.getenv('POSTGRES_USER', 'devmind'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'devmind123'),
        'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
        'CONN_MAX_AGE': 600,  # Reutilizar conexiones
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}

# ===========================================
# TESTING
# ===========================================
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# ===========================================
# LOGGING
# ===========================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'level': os.getenv('LOG_LEVEL', 'INFO'),
        },
    },
    'root': {
        'handlers': ['console'],
        'level': os.getenv('LOG_LEVEL', 'INFO'),
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'core': {
            'handlers': ['console'],
            'level': os.getenv('LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
    },
}

# ===========================================
# CONFIGURACIÓN ESPECÍFICA DE DEVMIND
# ===========================================
# Prefijo para nombres de tablas (opcional)
DEVMENT_TABLE_PREFIX = os.getenv('DEVMENT_TABLE_PREFIX', '')

# Timeout para queries largas (en segundos)
DEVMENT_QUERY_TIMEOUT = int(os.getenv('DEVMENT_QUERY_TIMEOUT', '30'))

# ===========================================
# CONFIGURACIÓN PARA TESTING
# ===========================================
if 'test' in sys.argv or 'pytest' in sys.modules or os.getenv('PYTEST_CURRENT_TEST'):
    # Forzar SQLite en memoria para tests rápidos y aislados
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'TEST': {
            'NAME': ':memory:',
        },
    }


    # Desactivar migraciones automáticas en tests
    class DisableMigrations:
        def __contains__(self, item):
            return True

        def __getitem__(self, item):
            return None


    MIGRATION_MODULES = DisableMigrations()

    # Password hashing más rápido para tests
    PASSWORD_HASHERS = [
        'django.contrib.auth.hashers.MD5PasswordHasher',
    ]

    # Desactivar logging verbose en tests
    LOGGING['root']['level'] = 'ERROR'
    LOGGING['loggers']['django']['level'] = 'ERROR'