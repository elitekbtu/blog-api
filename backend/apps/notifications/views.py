from django.db.models import QuerySet
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationSerializer
from apps.notifications.pagination import NotificationCursorPagination


class NotificationViewSet(ListModelMixin, GenericViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = NotificationCursorPagination

    def get_queryset(self) -> QuerySet[Notification]:
        return (
            Notification.objects.filter(recipient=self.request.user)
            .select_related("comment", "comment__author", "comment__post")
            .order_by("-created_at")
        )

    @action(methods=["GET"], detail=False, url_path="count")
    def count(self, request: Request) -> Response:
        # Polling is simple to implement and easy for clients to consume,
        # but it adds latency (updates arrive on the next poll) and increases
        # server load because clients keep sending repeated requests.
        # Polling is acceptable for low-frequency updates and modest scale.
        # If notifications must appear instantly or the number of clients grows,
        # WebSockets or SSE are usually a better fit.
        unread_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).count()
        return Response({"unread_count": unread_count}, status=status.HTTP_200_OK)

    @action(methods=["POST"], detail=False, url_path="read")
    def mark_all_as_read(self, request: Request) -> Response:
        updated_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).update(is_read=True)

        return Response(
            {"marked_as_read": updated_count},
            status=status.HTTP_200_OK,
        )
