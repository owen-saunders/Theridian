"""
Development settings for core project.
"""
import sys

# from .base import *
from .base import INSTALLED_APPS, LOGGING, MIDDLEWARE, THIRD_PARTY_APPS, dj_database_url

print("[WARNING] Using development settings")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Allow all hosts in development
ALLOWED_HOSTS = ["*"]

# CORS settings for development
CORS_ALLOW_ALL_ORIGINS = True

# Check if running python manage.py test
if "test" in sys.argv or "test" in "".join(sys.argv):
    print("[WARNING] Running tests, using test settings. Debug Toolbar disabled.")
    DEBUG = False
else:
    THIRD_PARTY_APPS += [
        "debug_toolbar",
    ]

# Database
DATABASES = {
    "default": dj_database_url.config(
        default="postgres://postgres:postgres@db:5432/theridian",
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Email backend for development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Django Debug Toolbar
if DEBUG:
    INTERNAL_IPS = [
        "127.0.0.1",
        "localhost",
    ]

    INSTALLED_APPS += [
        "debug_toolbar",
    ]

    MIDDLEWARE += [
        "debug_toolbar.middleware.DebugToolbarMiddleware",
    ]

    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK": lambda request: True,
    }

# Development logging - more verbose
LOGGING["root"]["level"] = "DEBUG"
LOGGING["loggers"]["apps"]["level"] = "DEBUG"

# Disable migrations during tests

if "test" in sys.argv:
    DATABASES["default"]["ENGINE"] = "django.db.backends.sqlite3"
    DATABASES["default"]["NAME"] = ":memory:"
