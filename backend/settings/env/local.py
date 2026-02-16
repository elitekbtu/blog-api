# Project modules
from settings.base import *  # noqa: F403


DEBUG = True
ALLOWED_HOSTS = []

# Database configuration
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "db.sqlite3",
    },
}

REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
