# Python modules
import json
import logging

# Third-party modules
from django.core.management.base import BaseCommand
import redis
from django.conf import settings

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Subscribe to Redis 'comments' channel and print incoming messages"

    def handle(self, *args, **options):
        """
        Main command handler that subscribes to the Redis 'comments' channel
        and prints incoming messages to the console.
        """
        self.stdout.write(self.style.SUCCESS("Starting Redis subscriber..."))
        self.stdout.write(
            self.style.SUCCESS(
                f"Subscribing to channel: comments (Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB})"
            )
        )

        try:
            redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True,
            )

            redis_client.ping()
            self.stdout.write(self.style.SUCCESS("✓ Connected to Redis"))

            pubsub = redis_client.pubsub()
            pubsub.subscribe("comments")

            self.stdout.write(self.style.SUCCESS("✓ Subscribed to 'comments' channel"))
            self.stdout.write(
                self.style.WARNING(
                    "\nListening for messages (Press Ctrl+C to stop)...\n"
                )
            )

            for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])

                        self.stdout.write(self.style.SUCCESS("\n" + "=" * 80))
                        self.stdout.write(
                            self.style.SUCCESS("New Comment Event Received!")
                        )
                        self.stdout.write(self.style.SUCCESS("=" * 80))
                        self.stdout.write(f"Comment ID: {data.get('id')}")
                        self.stdout.write(f"Post ID: {data.get('post_id')}")
                        self.stdout.write(f"Post Title: {data.get('post_title')}")
                        self.stdout.write(f"Author ID: {data.get('author_id')}")
                        self.stdout.write(f"Author Email: {data.get('author_email')}")
                        self.stdout.write(f"Body: {data.get('body')}")
                        self.stdout.write(f"Created At: {data.get('created_at')}")
                        self.stdout.write(self.style.SUCCESS("=" * 80 + "\n"))

                        logger.info(
                            f"Received comment event: comment_id={data.get('id')}"
                        )

                    except json.JSONDecodeError as e:
                        self.stdout.write(
                            self.style.ERROR(f"Failed to parse message: {e}")
                        )
                        self.stdout.write(f"Raw data: {message['data']}")
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"Error processing message: {e}")
                        )

        except redis.ConnectionError as e:
            self.stdout.write(self.style.ERROR(f"Failed to connect to Redis: {e}"))
            logger.error(f"Redis connection error: {e}", exc_info=True)

        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING("\n\nSubscriber stopped by user (Ctrl+C)")
            )
            logger.info("Redis subscriber stopped by user")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Unexpected error: {e}"))
            logger.error(f"Unexpected error in Redis subscriber: {e}", exc_info=True)

        finally:
            self.stdout.write(self.style.SUCCESS("\nClosing Redis connection..."))
            try:
                pubsub.close()
                redis_client.close()
                self.stdout.write(self.style.SUCCESS("✓ Redis connection closed"))
            except Exception:
                pass
