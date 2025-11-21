"""
Django settings for QueryCraft project.

This settings file is designed to work out-of-the-box for local development
with sensible defaults, while allowing environment variables to override
settings for Docker, staging, and production deployments.

╔════════════════════════════════════════════════════════════════╗
║ LOCAL DEVELOPMENT DEFAULTS (No Environment Variables Needed)   ║
╚════════════════════════════════════════════════════════════════╝

Prerequisites:
  • PostgreSQL running in Docker: docker compose up -d db
  • Ollama running in Docker: docker compose up -d ollama

Quick Start:
  just dev-services              # Start DB + Ollama
  python manage.py migrate
  python manage.py runserver

Defaults:
  ✓ SECRET_KEY: 'django-insecure-local-dev-key...' (dev only)
  ✓ DEBUG: True
  ✓ ALLOWED_HOSTS: ['localhost', '127.0.0.1', '0.0.0.0', '*']
  ✓ DATABASE: PostgreSQL @ localhost:5432 (connects to Docker)
  ✓ OLLAMA_BASE_URL: http://localhost:11434 (connects to Docker)
  ✓ OLLAMA_MODEL_NAME: sqlcoder-7b-2:local

╔════════════════════════════════════════════════════════════════╗
║ DOCKER/PRODUCTION (Override with Environment Variables)        ║
╚════════════════════════════════════════════════════════════════╝

Create .env file with:
  • SECRET_KEY=<random-key>          (required for production)
  • DEBUG=0                          (disable debug)
  • ALLOWED_HOSTS=example.com        (your domains)
  • POSTGRES_PASSWORD=<secure-pass>  (change default password)
  • OLLAMA_BASE_URL=http://ollama:11434 (auto-detected in Docker)

Environment Auto-Detection:
  - Database host: 'db' (Docker) or 'localhost' (local)
  - Ollama URL: 'http://ollama:11434' (Docker) or 'http://localhost:11434' (local)
"""

import os
from pathlib import Path
from urllib.parse import urlparse

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================
# Core Django Settings
# ============================================

# SECURITY WARNING: keep the secret key used in production secret!
# Default: Safe for local development only
# Production: Must set SECRET_KEY in environment variables
SECRET_KEY: str = os.environ.get(
    "SECRET_KEY", "django-insecure-local-dev-key-change-for-production-abcdef123456"
)

# SECURITY WARNING: don't run with debug turned on in production!
# Default: True (enabled for local development)
# Production: Set DEBUG=0 in environment variables
DEBUG: bool = os.environ.get("DEBUG", "1") == "1"

# Allowed hosts for the application
# Default: Permissive for local development
# Production: Set specific domains in ALLOWED_HOSTS environment variable
ALLOWED_HOSTS: list[str] = os.environ.get(
    "ALLOWED_HOSTS", "localhost,127.0.0.1,*"
).split(",")


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "querycraft",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "querycraft_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "querycraft_project.wsgi.application"


# ============================================
# Database Configuration
# ============================================
# Default: PostgreSQL (connects to Docker container)
# Override: Set DATABASE_URL for custom PostgreSQL connection
#
# Auto-detection:
#   - Running locally (default): Connects to localhost:5432 (Docker PostgreSQL)
#   - Running in Docker: Connects to db:5432 (internal network)
#
# Prerequisites for local development:
#   docker compose up -d db
#   # or
#   just dev-services
#
# Connection details (defaults):
#   Host:     localhost (local) or db (Docker)
#   Port:     5432
#   Database: querycraft
#   User:     querycraft
#   Password: querycraft_password
#
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases


# Get database configuration from environment
DATABASE_URL: str | None = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # Use explicitly provided DATABASE_URL
    try:
        parsed = urlparse(DATABASE_URL)
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": parsed.path[1:],  # Remove leading '/'
                "USER": parsed.username or "querycraft",
                "PASSWORD": parsed.password or "querycraft_password",
                "HOST": parsed.hostname or "db",
                "PORT": parsed.port or 5432,
            }
        }
    except Exception as e:
        # Raise error instead of falling back
        raise Exception(f"Failed to parse DATABASE_URL: {e}")
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("POSTGRES_DB", "querycraft"),
            "USER": os.environ.get("POSTGRES_USER", "querycraft"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "querycraft_password"),
            "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
            "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        }
    }


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ============================================
# Logging Configuration
# ============================================
# Comprehensive logging for query processing and debugging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{levelname}] {asctime} {name} {module}.{funcName}:{lineno} - {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "[{levelname}] {asctime} - {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs" / "querycraft.log",
            "formatter": "verbose",
        },
        "query_file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs" / "queries.log",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "querycraft": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "querycraft.services": {
            "handlers": ["console", "query_file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
}

# Ensure logs directory exists
logs_dir = BASE_DIR / "logs"
os.makedirs(logs_dir, exist_ok=True)

# ============================================
# Ollama Configuration
# ============================================
# Default: http://localhost:11434 (local Ollama installation)
# Override: Set OLLAMA_BASE_URL for custom URL
#

# Ollama base URL (auto-detected or from environment)
OLLAMA_BASE_URL: str = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

# Ollama model name for SQL code generation
# Default: sqlcoder-7b-2:local (optimized for SQL queries)
OLLAMA_MODEL_NAME: str = os.environ.get("OLLAMA_MODEL_NAME", "sqlcoder-7b-2:local")

# ============================================
# Configuration Summary (Debug Info)
# ============================================
# Print configuration summary on startup (only in DEBUG mode)
if DEBUG and os.environ.get("DJANGO_SETTINGS_MODULE"):
    import sys

    if "runserver" in sys.argv or "shell" in sys.argv:
        db_engine = DATABASES["default"].get("ENGINE")
        db_location = DATABASES["default"].get("HOST") or DATABASES["default"].get(
            "NAME"
        )

        # Determine configuration mode
        if DATABASE_URL:
            config_mode = "Explicit (DATABASE_URL)"
        else:
            config_mode = "PostgreSQL (Auto-detected: localhost)"

        # Check if using default SECRET_KEY
        using_default_key = "local-dev-key" in SECRET_KEY or "insecure" in SECRET_KEY

        print("\n" + "╔" + "═" * 68 + "╗")
        print("║" + " QueryCraft Configuration Summary".center(68) + "║")
        print("╚" + "═" * 68 + "╝")
        print(f"  Config Mode:     {config_mode}")
        print(
            f"  Debug Mode:      {'✓ Enabled' if DEBUG else '✗ Disabled'} (DEBUG={DEBUG})"
        )
        print(
            f"  Secret Key:      {'⚠ Using default (dev only)' if using_default_key else '✓ Custom key set'}"
        )
        print(f"  Database:        {db_engine} @ {db_location}")
        print(f"  Ollama URL:      {OLLAMA_BASE_URL}")
        print(f"  Ollama Model:    {OLLAMA_MODEL_NAME}")
        print("  " + "─" * 66)

        if using_default_key and not DEBUG:
            print("  ⚠ WARNING: Using default SECRET_KEY in production!")
            print("  " + "─" * 66)

        print("  Ready to accept connections at http://127.0.0.1:8000")
        print("╚" + "═" * 68 + "╝\n")
