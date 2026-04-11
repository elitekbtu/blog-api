from django.urls import path
from apps.notifications.websocket.consumer import CommentConsumer

url_patterns = [
    path("ws/comments/<slug:post_slug>/", CommentConsumer.as_asgi()),
]
