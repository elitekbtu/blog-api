# Project modules
from settings.base import *  # noqa: F403


DEBUG = False
ALLOWED_HOSTS = ["localhost"]

# Database configuration
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "db.sqlite3",
    },
}

REDIS_HOST = "redis"
REDIS_PORT = 6379
REDIS_DB = 0
