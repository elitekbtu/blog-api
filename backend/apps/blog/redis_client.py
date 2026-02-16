# Python modules
import json
import logging

# Third-party modules
import redis
from django.conf import settings

logger = logging.getLogger(__name__)

redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
)


def publish_comment_event(comment):
    try:
        event_data = {
            "id": comment.id,
            "post_id": comment.post.id,
            "post_title": comment.post.title,
            "author_id": comment.author.id,
            "author_email": comment.author.email,
            "body": comment.body,
            "created_at": comment.created_at.isoformat()
            if comment.created_at
            else None,
        }

        message = json.dumps(event_data)
        num_subscribers = redis_client.publish("comments", message)

        logger.info(
            f"Published comment event to Redis: comment_id={comment.id}, "
            f"subscribers={num_subscribers}"
        )

        return num_subscribers

    except Exception as e:
        logger.error(f"Failed to publish comment event: {e}", exc_info=True)
        return 0
