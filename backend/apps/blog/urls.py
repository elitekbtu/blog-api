# Third-party modules
from rest_framework.routers import DefaultRouter

# Django modules
from django.urls import path, include

# Project modules
from apps.blog.views import PostViewSet, CommentViewSet

router = DefaultRouter()
router.register(r"posts", PostViewSet, basename="post")
router.register(r"comments", CommentViewSet, basename="comment")

urlpatterns = [
    path("", include(router.urls)),
]
