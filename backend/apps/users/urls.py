# Third-party modules
from rest_framework.routers import DefaultRouter

# Django modules
from django.urls import path, include

# Project modules
from apps.users.views import CustomUserViewSet

router = DefaultRouter()
router.register(r"", CustomUserViewSet, basename="")

urlpatterns = [
    path("user/", include(router.urls)),
]
