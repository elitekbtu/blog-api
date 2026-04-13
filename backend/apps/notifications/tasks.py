import logging

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer

from apps.blog.models import Comment
from apps.notifications.models import Notification

logger = logging.getLogger(__name__)


@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def process_new_comment(comment_id: int) -> None:
    # Automatic retries matter for comment side effects because both database writes
    # and realtime channel delivery can fail transiently; retries help keep
    # notifications and websocket events consistent without manual intervention.
    try:
        comment = Comment.objects.select_related("post", "author").get(id=comment_id)
    except Comment.DoesNotExist:
        logger.warning(
            "Skipping new-comment processing: comment_id=%s not found", comment_id
        )
        return

    post = comment.post

    if post.author_id != comment.author_id:
        Notification.objects.get_or_create(
            recipient_id=post.author_id,
            comment=comment,
        )

    channel_layer = get_channel_layer()
    if channel_layer is None:
        logger.warning("Channel layer unavailable for comment_id=%s", comment.id)
        return

    payload = {
        "comment_id": comment.id,
        "author": {
            "id": comment.author.id,
            "email": comment.author.email,
        },
        "body": comment.body,
        "created_at": comment.created_at.isoformat() if comment.created_at else None,
    }

    async_to_sync(channel_layer.group_send)(
        f"post_{post.slug}-messages",
        {
            "type": "comment_message",
            "comment": payload,
            "slug": post.slug,
        },
    )


@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def clear_expired_notifications() -> None:
    # Automatic retries matter for cleanup jobs because transient database issues
    # should not leave retention tasks permanently missed for that day.
    from datetime import timedelta
    from django.utils import timezone

    expiration_threshold = timezone.now() - timedelta(days=30)
    deleted_count, _ = Notification.objects.filter(
        created_at__lt=expiration_threshold
    ).delete()
    logger.info("Cleared expired notifications: deleted_count=%s", deleted_count)
