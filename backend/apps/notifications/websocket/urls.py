from django.urls import path
from apps.notifications.websocket.consumer import CommentConsumer

url_patterns = [
    path("ws/posts/<slug:post_slug>/comments/", CommentConsumer.as_asgi()),
]
