# Project modules
from settings.base import *  # noqa: F403
from decouple import config


DEBUG = False
ALLOWED_HOSTS = ["localhost"]

# Database configuration
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": config("BLOG_SQLITE_PATH", default="db.sqlite3", cast=str),
    },
}
