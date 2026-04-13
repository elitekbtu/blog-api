import json
from typing import Any

from django.conf import settings
from redis.asyncio import Redis

from apps.blog.models import Post

POST_PUBLISHED_CHANNEL = "posts:published"


async def publish_post_published_event(data: dict[str, Any]) -> None:
    redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        await redis.publish(POST_PUBLISHED_CHANNEL, json.dumps(data))
    finally:
        await redis.aclose()


def build_post_published_payload(post: Post) -> dict:
    return {
        "post_id": post.id,
        "title": post.title,
        "slug": post.slug,
        "author": {
            "id": post.author.id,
            "email": post.author.email,
        },
        "published_at": post.updated_at.isoformat() if post.updated_at else None,
    }
