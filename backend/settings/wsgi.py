# Python modules
import os

# Project modules
from settings.conf import ENV_ID_POSSIBLE_OPTIONS, BLOG_ENV_ID
from django.core.wsgi import get_wsgi_application

assert BLOG_ENV_ID in ENV_ID_POSSIBLE_OPTIONS, (
    f"Set correct BLOG_ENV_ID env var. Possible options: {ENV_ID_POSSIBLE_OPTIONS}"
)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.base")

application = get_wsgi_application()
