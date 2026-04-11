# Python modules
import os

# Third-party modules
from channels.routing import ProtocolTypeRouter, URLRouter
from core.middleware.websocket import AuthWebsocketMiddleware
from apps.notifications.websocket.urls import url_patterns

# Project modules
from settings.conf import BLOG_ENV_ID, ENV_ID_POSSIBLE_OPTIONS
from django.core.asgi import get_asgi_application


assert BLOG_ENV_ID in ENV_ID_POSSIBLE_OPTIONS, (
    f"Set correct BLOG_ENV_ID env var. Possible options: {ENV_ID_POSSIBLE_OPTIONS}"
)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.base")

django_asgi_application = get_asgi_application()

application = ProtocolTypeRouter(
    {
        "http": django_asgi_application,
        "websocket": AuthWebsocketMiddleware(URLRouter(url_patterns)),
    }
)
