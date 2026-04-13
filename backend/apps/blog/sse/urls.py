from django.urls import path

from apps.blog.sse.views import PostStreamView

urlpatterns = [
    path("posts/stream/", PostStreamView.as_view(), name="posts-stream"),
]
