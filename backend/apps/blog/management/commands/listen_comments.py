# Python modules
import asyncio
import json
import logging

# Third-party modules
from django.core.management.base import BaseCommand
import redis.asyncio as redis_async
from django.conf import settings

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Subscribe to Redis 'comments' channel and print incoming messages"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting Redis subscriber..."))
        self.stdout.write(
            self.style.SUCCESS(
                f"Subscribing to channel: comments (Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB})"
            )
        )

        try:
            asyncio.run(self._listen_comments())
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING("\n\nSubscriber stopped by user (Ctrl+C)")
            )
            logger.info("Redis subscriber stopped by user")

    async def _listen_comments(self) -> None:
        # Async keeps the event loop responsive for network I/O; a sync listener would block on Redis reads and reduce concurrency.
        redis_client = redis_async.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
        )
        pubsub = None

        try:
            await redis_client.ping()
            self.stdout.write(self.style.SUCCESS("✓ Connected to Redis"))

            pubsub = redis_client.pubsub()
            await pubsub.subscribe("comments")

            self.stdout.write(self.style.SUCCESS("✓ Subscribed to 'comments' channel"))
            self.stdout.write(
                self.style.WARNING(
                    "\nListening for messages (Press Ctrl+C to stop)...\n"
                )
            )

            while True:
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0,
                )

                if message is None:
                    await asyncio.sleep(0.05)
                    continue

                self._print_comment_event(message)

        except redis_async.ConnectionError as exc:
            self.stdout.write(self.style.ERROR(f"Failed to connect to Redis: {exc}"))
            logger.error(f"Redis connection error: {exc}", exc_info=True)
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"Unexpected error: {exc}"))
            logger.error(f"Unexpected error in Redis subscriber: {exc}", exc_info=True)
        finally:
            self.stdout.write(self.style.SUCCESS("\nClosing Redis connection..."))
            try:
                if pubsub is not None:
                    await pubsub.unsubscribe("comments")
                    await pubsub.close()
                await redis_client.aclose()
                self.stdout.write(self.style.SUCCESS("✓ Redis connection closed"))
            except Exception:
                pass

    def _print_comment_event(self, message: dict) -> None:
        try:
            data = json.loads(message["data"])
            required_keys = ("post_slug", "author_id", "body")
            missing_keys = [key for key in required_keys if not data.get(key)]

            if missing_keys:
                self.stdout.write(
                    self.style.ERROR(
                        f"Comment event missing required fields: {', '.join(missing_keys)}"
                    )
                )
                self.stdout.write(f"Raw data: {message['data']}")
                return

            self.stdout.write(self.style.SUCCESS("\n" + "=" * 80))
            self.stdout.write(self.style.SUCCESS("New Comment Event Received!"))
            self.stdout.write(self.style.SUCCESS("=" * 80))
            self.stdout.write(f"Comment ID: {data.get('id')}")
            self.stdout.write(f"Post Slug: {data.get('post_slug')}")
            self.stdout.write(f"Post ID: {data.get('post_id')}")
            self.stdout.write(f"Post Title: {data.get('post_title')}")
            self.stdout.write(f"Author ID: {data.get('author_id')}")
            self.stdout.write(f"Author Email: {data.get('author_email')}")
            self.stdout.write(f"Body: {data.get('body')}")
            self.stdout.write(f"Created At: {data.get('created_at')}")
            self.stdout.write(self.style.SUCCESS("=" * 80 + "\n"))

            logger.info(f"Received comment event: comment_id={data.get('id')}")

        except json.JSONDecodeError as exc:
            self.stdout.write(self.style.ERROR(f"Failed to parse message: {exc}"))
            self.stdout.write(f"Raw data: {message.get('data')}")
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"Error processing message: {exc}"))
