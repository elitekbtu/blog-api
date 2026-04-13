# Project modules
import os
from datetime import timedelta
from urllib.parse import urlparse

from settings.conf import *  # noqa: F403
from django.utils.translation import gettext_lazy as _

"""
Path configurations
"""

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
ROOT_URLCONF = "settings.urls"
WSGI_APPLICATION = "settings.wsgi.application"
ASGI_APPLICATION = "settings.asgi.application"
AUTH_USER_MODEL = "users.CustomUser"

REDIS_URL = BLOG_REDIS_URL  # noqa: F405
redis_parsed = urlparse(REDIS_URL)
REDIS_HOST = redis_parsed.hostname or "localhost"
REDIS_PORT = redis_parsed.port or 6379
REDIS_DB = int((redis_parsed.path or "/0").lstrip("/") or 0)

"""
Apps
"""

DJANGO_AND_THIRD_PARTY_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "channels",
    "django_extensions",
    "drf_spectacular",
]

PROJECT_APPS = [
    "apps.abstract",
    "apps.blog",
    "apps.users",
    "apps.notifications",
]

INSTALLED_APPS = DJANGO_AND_THIRD_PARTY_APPS + PROJECT_APPS


"""
Logging
"""

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "[{levelname}] {message}",
            "style": "{",
        },
        "verbose": {
            "format": "[{asctime}] {levelname} "
            "{name} {module}.{funcName}: {lineno} - {message}",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "simple",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "WARNING",
            "filename": os.path.join(LOG_DIR, "app.log"),
            "maxBytes": 5 * 1024 * 1024,  # 10 MB
            "backupCount": 3,
            "formatter": "verbose",
            "encoding": "utf-8",
        },
        "debug_only": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "filename": os.path.join(LOG_DIR, "debug_requests.log"),
            "maxBytes": 5 * 1024 * 1024,  # 10 MB
            "backupCount": 3,
            "formatter": "verbose",
            "filters": ["require_debug_true"],
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "apps.users": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "apps.blog": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["file", "debug_only"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

"""
Simple JWT
"""

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,  # noqa: F405
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
}

"""
Django Rest Framework
"""

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.CursorPagination",
    "PAGE_SIZE": 100,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

"""
Documentation Settings
"""

SPECTACULAR_SETTINGS = {
    "TITLE": "Blog API",
    "DESCRIPTION": "Blog API system",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": True,
    "TAGS": [
        {
            "name": "Auth",
            "description": "Authentication, registration, profile, and user preference endpoints.",
        },
        {
            "name": "Posts",
            "description": "Post CRUD and post-scoped operations.",
        },
        {
            "name": "Comments",
            "description": "Comment listing, retrieval, and moderation endpoints.",
        },
        {
            "name": "Stats",
            "description": "List and feed-like endpoints that expose aggregate/paginated activity views.",
        },
    ],
}

"""
Caching
"""

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": "blog",
        "TIMEOUT": 300,
    }
}

"""
Celery
"""

CELERY_BROKER_URL = BLOG_CELERY_BROKER_URL  # noqa: F405
CELERY_RESULT_BACKEND = BLOG_CELERY_BROKER_URL  # noqa: F405

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [REDIS_URL]},
    }
}
"""
Middleware | Templates | Validators
"""

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.language.LanguageMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
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


"""
Internalizations
"""

LANGUAGE_CODE = "en"
TIME_ZONE = "UTC"

LANGUAGES = [
    ("en", _("English")),
    ("ru", _("Russian")),
    ("kk", _("Kazakh")),
]

LOCALE_PATHS = [
    os.path.join(BASE_DIR, "locale"),
]

USE_I18N = True
USE_TZ = True

"""
Static | Media
"""

STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")
MEDIA_URL = "media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

"""
Email
"""

DEFAULT_FROM_EMAIL = "noreply@blogapi.com"
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
