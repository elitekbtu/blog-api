# Third-party modules

from decouple import config

"""
Enviorenment id
"""

ENV_ID_POSSIBLE_OPTIONS = ("local", "prod")

BLOG_ENV_ID = config("BLOG_ENV_ID", cast=str)
SECRET_KEY = config("SECRET_KEY", cast=str)
