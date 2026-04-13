"""  
Configuration module for environment settings.

Loads environment-specific configuration using python-decouple.
"""

# Third-party modules
from decouple import config

"""
Environment ID configuration
"""

# Possible environment options
ENV_ID_POSSIBLE_OPTIONS = ("local", "prod")

# Current environment ID from environment variable
BLOG_ENV_ID = config("BLOG_ENV_ID", cast=str)

# Django secret key from environment variable
SECRET_KEY = config("SECRET_KEY", cast=str)

# Redis and Celery
BLOG_REDIS_URL = config(
    "BLOG_REDIS_URL",
    default="redis://localhost:6379/0",
    cast=str,
)
BLOG_CELERY_BROKER_URL = config(
    "BLOG_CELERY_BROKER_URL",
    default="redis://localhost:6379/1",
    cast=str,
)

# Flower
BLOG_FLOWER_USER = config("BLOG_FLOWER_USER", default="admin", cast=str)
BLOG_FLOWER_PASSWORD = config("BLOG_FLOWER_PASSWORD", default="changeme", cast=str)

# Startup options
BLOG_SEED_DB = config("BLOG_SEED_DB", default=False, cast=bool)
BLOG_SQLITE_PATH = config("BLOG_SQLITE_PATH", default="db.sqlite3", cast=str)
