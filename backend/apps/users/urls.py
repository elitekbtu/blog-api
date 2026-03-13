# Third-party modules
from rest_framework.routers import DefaultRouter


# Django modules
from django.urls import path, include

# Project modules
from apps.users.views import CustomUserViewSet, UserPreferencesViewSet

router = DefaultRouter()
router.register(r"", CustomUserViewSet, basename="user")
preferences_view = UserPreferencesViewSet.as_view(
    {
        "get": "retrieve",
        "patch": "partial_update",
    }
)

urlpatterns = [
    path("user/", include(router.urls)),
    path("user/preferences/", preferences_view, name="user-preferences"),
]