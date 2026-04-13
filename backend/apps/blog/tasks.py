import logging
from datetime import timedelta

from asgiref.sync import async_to_sync
from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone

from apps.blog.models import Comment, Post
from apps.blog.sse.publisher import build_post_published_payload, publish_post_published_event

logger = logging.getLogger(__name__)

User = get_user_model()


@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def invalidate_posts_cache_task() -> None:
    # Automatic retries matter for cache invalidation because cache backends can be
    # temporarily unavailable; retries reduce stale-data windows after writes.
    cache.delete("published_posts_list")
    logger.info("Invalidated posts cache key: published_posts_list")


@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def publish_scheduled_posts() -> None:
    # Automatic retries matter for scheduled publishing because temporary DB/Redis
    # failures should not permanently skip a publish window for due posts.
    now = timezone.now()
    scheduled_posts = Post.objects.filter(
        status=Post.Status.SCHEDULED,
        publish_at__isnull=False,
        publish_at__lte=now,
    )

    for post in scheduled_posts:
        post.status = Post.Status.PUBLISHED
        post.save(update_fields=["status", "updated_at"])

        payload = build_post_published_payload(post)
        async_to_sync(publish_post_published_event)(payload)

        logger.info("Published scheduled post: post_id=%s", post.id)


@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def generate_daily_stats() -> None:
    # Automatic retries matter for analytics reporting because intermittent backend
    # outages should not cause gaps in daily operational metrics.
    since = timezone.now() - timedelta(hours=24)

    posts_count = Post.objects.filter(created_at__gte=since).count()
    comments_count = Comment.objects.filter(created_at__gte=since).count()
    users_count = User.objects.filter(date_joined__gte=since).count()

    logger.info(
        "Daily stats (last 24h): posts=%s, comments=%s, users=%s",
        posts_count,
        comments_count,
        users_count,
    )
