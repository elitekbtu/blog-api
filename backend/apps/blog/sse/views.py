from typing import AsyncGenerator

from django.conf import settings
from django.http import StreamingHttpResponse
from django.views import View
from redis.asyncio import Redis

POST_PUBLISHED_CHANNEL = "posts:published"


# Why SSE better than WebSockets for this use case:
# 1. Simplicity: SSE is built on top of standard HTTP, making it
#    easier to implement and maintain compared to WebSockets, which require a separate protocol and connection management.
# 2. Server-to-Client Communication: SSE is designed for unidirectional communication from
#    server to client, which fits our use case of sending real-time updates about new posts. WebSockets are bidirectional, which adds unnecessary complexity for this scenario.
# 3. Scalability: SSE can be more scalable for broadcasting updates to many clients,
#    as it uses a single HTTP connection per client, while WebSockets may require more resources to manage multiple connections.s
class PostStreamView(View):
    async def get(self, request, *args, **kwargs):
        async def event_stream() -> AsyncGenerator[str, None]:
            redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
            pubsub = redis.pubsub()

            try:
                await pubsub.subscribe(POST_PUBLISHED_CHANNEL)

                while True:
                    message = await pubsub.get_message(
                        ignore_subscribe_messages=True,
                        timeout=15.0,
                    )

                    if message is None:
                        yield ": keepalive\n\n"
                        continue

                    payload = message["data"]
                    yield f"event: post_published\n"
                    yield f"data: {payload}\n\n"

            finally:
                await pubsub.unsubscribe(POST_PUBLISHED_CHANNEL)
                await pubsub.aclose()
                await redis.aclose()

        response = StreamingHttpResponse(
            streaming_content=event_stream(),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        response["Connection"] = "keep-alive"
        response["X-Accel-Buffering"] = "no"
        return response
