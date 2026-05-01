# Python modules
import json
from logging import getLogger
from typing import Optional, Any


# Third-party modules
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer


logger = getLogger(__name__)

AUTHENTICATION_ERROR_CODE = 4001
POST_SLUG_NOT_FOUND_ERROR_CODE = 4004


class CommentConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling real-time comment updates on blog posts.
    """

    async def connect(self, *args: tuple[Any], **kwargs: dict[str, Any]) -> None:
        self.group_name = None
        self.user_id = None
        self.post_slug = None

        from django.contrib.auth.models import AnonymousUser
        from apps.users.models import CustomUser
        from apps.blog.models import Post

        user: CustomUser | AnonymousUser = self.scope.get("user", AnonymousUser())
        if user.is_authenticated:
            self.user_id: int = user.id

            logger.info(f"User {self.user_id} connected to WebSocket")

            self.post_slug: Optional[str] = self.scope["url_route"]["kwargs"][
                "post_slug"
            ]

            logger.info(
                f"User {self.user_id} is trying to connect to post slug {self.post_slug}"
            )
            if not self.post_slug:
                logger.warning(
                    f"User {self.user_id} tried to connect without a post slug, sending error message and closing connection"
                )
                logger.warning(
                    f"User {self.user_id} tried to connect without a post slug, closing connection"
                )
                await self.close(code=POST_SLUG_NOT_FOUND_ERROR_CODE)
                return
            logger.info(
                f"User {self.user_id} wants to connect to post slug {self.post_slug}"
            )

            post: Optional[Post] = await database_sync_to_async(
                lambda: Post.objects.filter(slug=self.post_slug).first()
            )()
            if not post:
                logger.warning(
                    f"User {self.user_id} tried to connect to non-existent post with slug {self.post_slug}, sending error message and closing connection"
                )
                logger.warning(
                    f"User {self.user_id} tried to connect to non-existent post with slug {self.post_slug}, closing connection"
                )
                await self.close(code=POST_SLUG_NOT_FOUND_ERROR_CODE)
                return

            self.group_name = f"post_{self.post_slug}-messages"
            logger.info(
                f"User {self.user_id} added to group {self.group_name} for post slug {self.post_slug}"
            )
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()

        else:
            logger.warning(
                "Unauthenticated user tried to connect to WebSocket, sending error message and closing connection"
            )
            await self.close(code=AUTHENTICATION_ERROR_CODE)
            logger.warning(
                "Unauthenticated user tried to connect to WebSocket, sent error message and closed connection"
            )

    async def disconnect(
        self, close_code, *args: tuple[Any], **kwargs: dict[str, Any]
    ) -> None:
        logger.info(f"User {self.user_id} disconnected from WebSocket")

        if self.post_slug and self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            logger.info(
                f"User {self.user_id} removed from group {self.group_name} code: {close_code}"
            )
        self.group_name = None
        self.user_id = None
        self.post_slug = None

    async def comment_message(self, event: dict[str, Any]) -> None:
        comment_id = event["comment"].get("comment_id")
        self.post_slug = event.get("slug")
        author_id = event["comment"]["author"].get("id")

        logger.info(
            f"User {self.user_id} received new comment message for post slug {self.post_slug} with comment id {comment_id} from author id {author_id}"
        )

        await self.send(
            text_data=json.dumps(event["comment"]),
        )
