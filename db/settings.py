# devmind-core/db/settings.py
"""
Configuración mínima de Django para DevMind Core.
"""

import os
from pathlib import Path

# ✅ Leer variables de entorno para SQLite
USE_SQLITE = os.getenv("DEVMENT_TEST_USE_SQLITE") == "True"
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "devmind-secret-key-change-in-production")
DEBUG = os.getenv("DEBUG", "True") == "True"

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "db",  # Tu app con los modelos
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "db.urls" if (BASE_DIR / "db" / "urls.py").exists() else None

# ✅ CONFIGURACIÓN DE BASE DE DATOS DINÁMICA
if USE_SQLITE or "sqlite" in DATABASE_URL.lower():
    # SQLite para pruebas
    db_name = DATABASE_URL.replace("sqlite:///", "") if DATABASE_URL else "devmind_test.db"
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / db_name if not db_name.startswith("/") else db_name,
        }
    }
else:
    # PostgreSQL para producción
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "HOST": os.getenv("POSTGRES_HOST", "localhost"),
            "PORT": os.getenv("POSTGRES_PORT", "5432"),
            "NAME": os.getenv("POSTGRES_DB", "devmind"),
            "USER": os.getenv("POSTGRES_USER", "devmind"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", "devmind123"),
        }
    }

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": os.getenv("LOG_LEVEL", "INFO"),
    },
}