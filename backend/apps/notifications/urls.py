from django.urls import path

from apps.notifications.views import NotificationViewSet

urlpatterns = [
    path(
        "notifications/",
        NotificationViewSet.as_view({"get": "list"}),
        name="notifications-list",
    ),
    path(
        "notifications/count/",
        NotificationViewSet.as_view({"get": "count"}),
        name="notifications-count",
    ),
    path(
        "notifications/read/",
        NotificationViewSet.as_view({"post": "mark_all_as_read"}),
        name="notifications-read",
    ),
]
