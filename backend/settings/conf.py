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
