"""
Production settings for core project.
"""
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from .base import *

print("[WARNING] Using production settings")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_HSTS_SECONDS = 31536000
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = "DENY"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": os.environ["APP_DATABASE_HOST"],
        "PORT": os.environ.get("APP_DATABASE_PORT", ""),
        "NAME": os.environ["APP_DATABASE_NAME"],
        "USER": os.environ["APP_DATABASE_USER"],
        "PASSWORD": os.environ["APP_DATABASE_PASSWORD"],
    }
}

# Database connection pooling
DATABASES["default"]["CONN_MAX_AGE"] = 60


# Static files for production
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Email configuration for production
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = env("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env(
    "DEFAULT_FROM_EMAIL", default="56914238+owen-saunders@users.noreply.github.com"
)

# Sentry configuration
SENTRY_DSN = env("SENTRY_DSN", default="")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(
                transaction_style="url",
                middleware_spans=True,
                signals_spans=True,
            ),
            CeleryIntegration(
                monitor_beat_tasks=True,
                propagate_traces=True,
            ),
            RedisIntegration(),
        ],
        traces_sample_rate=0.1,
        send_default_pii=True,
        environment="production",
        release=env("HEROKU_SLUG_COMMIT", default="unknown"),
    )

# Disable Django's own CORS to rely on external solutions
CORS_ALLOW_ALL_ORIGINS = False

# Production logging
LOGGING["handlers"]["console"]["level"] = "INFO"
LOGGING["root"]["level"] = "INFO"
LOGGING["loggers"]["django"]["level"] = "WARNING"
LOGGING["loggers"]["apps"]["level"] = "INFO"

# Cache settings for production
CACHES["default"]["OPTIONS"]["CONNECTION_POOL_KWARGS"] = {
    "max_connections": 50,
    "retry_on_timeout": True,
}

# Session security
SESSION_COOKIE_AGE = 86400  # 1 day
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# CSRF settings
CSRF_COOKIE_AGE = 86400
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS", default=[])

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
