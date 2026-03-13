# Python modules
import asyncio
from datetime import datetime
from typing import Any
import logging
from zoneinfo import ZoneInfo


# Third-party modules
import httpx
from asgiref.sync import async_to_sync
from rest_framework.viewsets import ViewSet
from rest_framework.views import APIView
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response as DRFResponse
from rest_framework.request import Request as DRFRequest
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_503_SERVICE_UNAVAILABLE,
)
from rest_framework.exceptions import NotFound, PermissionDenied
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    inline_serializer,
)

# Django modules
from django.db.models import Q
from django.core.cache import cache

# Project modules
from apps.blog.models import Post, Comment
from apps.blog.serializers import (
    PostListSerializer,
    PostDetailSerializer,
    PostCreateUpdateSerializer,
    CommentSerializer,
)
from apps.blog.permissions import IsAuthorOrReadOnly
from apps.abstract.pagination import DefaultPagination
from apps.abstract.ratelimit import ratelimit

from utils.cache_key import build_posts_cache_key

logger = logging.getLogger(__name__)

BlogUnauthorizedErrorResponse = inline_serializer(
    name="BlogUnauthorizedErrorResponse",
    fields={
        "detail": serializers.CharField(),
    },
)

BlogForbiddenErrorResponse = inline_serializer(
    name="BlogForbiddenErrorResponse",
    fields={
        "detail": serializers.CharField(required=False),
    },
)

BlogNotFoundErrorResponse = inline_serializer(
    name="BlogNotFoundErrorResponse",
    fields={
        "detail": serializers.CharField(),
    },
)

BlogRateLimitErrorResponse = inline_serializer(
    name="BlogRateLimitErrorResponse",
    fields={
        "detail": serializers.CharField(),
    },
)

BlogValidationErrorResponse = inline_serializer(
    name="BlogValidationErrorResponse",
    fields={
        "detail": serializers.CharField(required=False),
        "errors": serializers.DictField(required=False),
    },
)


class PostViewSet(ViewSet):
    """
    ViewSet for Post model:
    - GET /api/posts/ — List published posts (no auth required)
    - POST /api/posts/ — Create post (auth required)
    - GET /api/posts/{slug}/ — Get single post (no auth required)
    - PATCH /api/posts/{slug}/ — Update own post (auth required)
    - DELETE /api/posts/{slug}/ — Delete own post (auth required)
    - GET /api/posts/{slug}/comments/ — List comments (no auth required)
    - POST /api/posts/{slug}/comments/ — Add comment (auth required)
    """

    lookup_field: str = "slug"
    permission_classes: tuple = (IsAuthorOrReadOnly,)
    pagination_class = DefaultPagination
    serializer_class = PostDetailSerializer

    def get_serializer_class(self):
        action = getattr(self, "action", None)
        if action == "list":
            return PostListSerializer
        if action in {"create", "partial_update"}:
            return PostCreateUpdateSerializer
        if action == "comments":
            return CommentSerializer
        return self.serializer_class

    def get_permissions(self):
        return [permission() for permission in self.permission_classes]

    def check_permissions(self, request):
        for permission in self.get_permissions():
            if not permission.has_permission(request, self):
                raise PermissionDenied()

    def check_object_permissions(self, request, obj):
        for permission in self.get_permissions():
            if not permission.has_object_permission(request, self, obj):
                raise PermissionDenied()

    @extend_schema(
        tags=["Posts", "Stats"],
        summary="List posts visible to current user",
        description=(
            "Returns a paginated list of posts. Authentication is optional. Anonymous users only see "
            "published posts; authenticated users see published posts plus their own drafts. "
            "Side effects: for anonymous requests, list responses are cached for 60 seconds by a "
            "query-dependent cache key; authenticated responses are not cached. Language behavior: "
            "category names are localized by active language. Timezone behavior: `created_at` values "
            "are formatted using authenticated user's timezone; anonymous users receive UTC-based formatting.\n\n"
            "Request example:\n"
            "GET /api/posts/?cursor=<cursor>&page_size=10\n\n"
            "Response example (200):\n"
            "{\n"
            "  \"next\": null,\n"
            "  \"previous\": null,\n"
            "  \"results\": [\n"
            "    {\n"
            "      \"id\": 1,\n"
            "      \"title\": \"Django Tips\",\n"
            "      \"slug\": \"django-tips\",\n"
            "      \"status\": \"published\"\n"
            "    }\n"
            "  ]\n"
            "}"
        ),
        responses={
            200: OpenApiResponse(
                response=PostListSerializer(many=True),
                description="Posts listed successfully (typically paginated).",
            ),
        },
        examples=[
            OpenApiExample(
                "Post List Success",
                value={
                    "next": None,
                    "previous": None,
                    "results": [
                        {
                            "id": 1,
                            "author": {
                                "id": 7,
                                "email": "alice@example.com",
                                "first_name": "Alice",
                                "last_name": "Smith",
                                "avatar": None,
                            },
                            "title": "Django Tips",
                            "slug": "django-tips",
                            "category": {
                                "id": 2,
                                "name": "Backend",
                                "slug": "backend",
                            },
                            "tags": [{"id": 3, "name": "django", "slug": "django"}],
                            "status": "published",
                            "created_at": "14:20 13-03-2026",
                        }
                    ],
                },
                response_only=True,
                status_codes=["200"],
            )
        ],
    )
    def list(
        self,
        request: DRFRequest,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        self.check_permissions(request)

        user_info = (
            f"user_id={request.user.id}"
            if request.user.is_authenticated
            else "anonymous"
        )
        logger.info(f"Listing posts requested by {user_info}")

        if request.user.is_authenticated:
            queryset = Post.objects.filter(
                Q(status=Post.Status.PUBLISHED) | Q(author=request.user)
            )
            logger.debug(f"Posts queryset count: {queryset.count()} for {user_info}")

            paginator = self.pagination_class()
            page = paginator.paginate_queryset(queryset, request, view=self)

            if page is not None:
                serializer: PostListSerializer = PostListSerializer(
                    page, many=True, context={"request": request}
                )
                return paginator.get_paginated_response(serializer.data)

            serializer: PostListSerializer = PostListSerializer(
                queryset, many=True, context={"request": request}
            )
            return DRFResponse(
                data=serializer.data,
                status=HTTP_200_OK,
            )

        cache_key = build_posts_cache_key(request)
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            logger.info(f"Returning cached posts list for {user_info}")
            return DRFResponse(
                data=cached_data,
                status=HTTP_200_OK,
            )

        logger.info(f"Cache miss - fetching posts from database for {user_info}")
        queryset = Post.objects.filter(status=Post.Status.PUBLISHED)
        logger.debug(f"Posts queryset count: {queryset.count()} for {user_info}")

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)

        if page is not None:
            serializer: PostListSerializer = PostListSerializer(
                page, many=True, context={"request": request}
            )
            response_data = paginator.get_paginated_response(serializer.data).data
            cache.set(cache_key, response_data, 60)
            logger.info("Cached posts list for 60 seconds")
            return DRFResponse(
                data=response_data,
                status=HTTP_200_OK,
            )

        serializer: PostListSerializer = PostListSerializer(
            queryset, many=True, context={"request": request}
        )
        response_data = serializer.data
        cache.set(cache_key, response_data, 60)
        logger.info("Cached posts list for 60 seconds")
        return DRFResponse(
            data=response_data,
            status=HTTP_200_OK,
        )

    @extend_schema(
        tags=["Posts"],
        summary="Create a new post",
        description=(
            "Creates a post owned by the authenticated user. Authentication is required. "
            "Side effects: invalidates post list cache key `published_posts_list` after successful "
            "creation and writes audit logs. Language behavior: validation errors can be localized. "
            "Timezone behavior: response datetime fields follow serializer formatting rules.\n\n"
            "Request example:\n"
            "POST /api/posts/\n"
            "Authorization: Bearer <jwt-access-token>\n"
            "{\n"
            "  \"title\": \"Django Tips\",\n"
            "  \"body\": \"Use serializers wisely.\",\n"
            "  \"category\": 2,\n"
            "  \"tags\": [3],\n"
            "  \"status\": \"published\"\n"
            "}\n\n"
            "Response example (201):\n"
            "{\n"
            "  \"id\": 15,\n"
            "  \"title\": \"Django Tips\",\n"
            "  \"slug\": \"django-tips\",\n"
            "  \"status\": \"published\"\n"
            "}"
        ),
        request=PostCreateUpdateSerializer,
        responses={
            201: OpenApiResponse(
                response=PostCreateUpdateSerializer,
                description="Post created successfully.",
            ),
            400: OpenApiResponse(
                response=BlogValidationErrorResponse,
                description="Invalid post payload.",
            ),
            401: OpenApiResponse(
                response=BlogUnauthorizedErrorResponse,
                description="Authentication required.",
            ),
            429: OpenApiResponse(
                response=BlogRateLimitErrorResponse,
                description="Too many post creation requests.",
            ),
        },
        examples=[
            OpenApiExample(
                "Create Post Request",
                value={
                    "title": "Django Tips",
                    "body": "Use serializers wisely.",
                    "category": 2,
                    "tags": [3],
                    "status": "published",
                },
                request_only=True,
            ),
            OpenApiExample(
                "Create Post Success",
                value={
                    "id": 15,
                    "author": {
                        "id": 7,
                        "email": "alice@example.com",
                        "first_name": "Alice",
                        "last_name": "Smith",
                        "avatar": None,
                    },
                    "title": "Django Tips",
                    "slug": "django-tips",
                    "body": "Use serializers wisely.",
                    "category": 2,
                    "tags": [3],
                    "status": "published",
                },
                response_only=True,
                status_codes=["201"],
            ),
            OpenApiExample(
                "Create Post Unauthorized",
                value={"detail": "Authentication required."},
                response_only=True,
                status_codes=["401"],
            ),
            OpenApiExample(
                "Create Post Rate Limit",
                value={"detail": "Too many requests. Try again later."},
                response_only=True,
                status_codes=["429"],
            ),
        ],
    )
    @ratelimit(key_func=lambda r: str(r.user.id) if r.user.is_authenticated else "anonymous", rate="20/m", method="POST")
    def create(
        self,
        request: DRFRequest,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        self.check_permissions(request)

        if not request.user.is_authenticated:
            logger.warning("Unauthorized attempt to create post")
            return DRFResponse(
                data={"detail": "Authentication required."},
                status=HTTP_401_UNAUTHORIZED,
            )

        logger.info(f"Creating post by user_id={request.user.id}")

        serializer: PostCreateUpdateSerializer = PostCreateUpdateSerializer(
            data=request.data,
        )

        if serializer.is_valid():
            post = serializer.save(author=request.user)

            cache.delete("published_posts_list")
            logger.info("Invalidated published posts cache after post creation")

            logger.info(
                f"Post created successfully: post_id={post.id}, "
                f"slug={post.slug}, author_id={request.user.id}"
            )
            return DRFResponse(
                data=serializer.data,
                status=HTTP_201_CREATED,
            )

        logger.error(
            f"Post creation failed for user_id={request.user.id}: {serializer.errors}"
        )
        return DRFResponse(
            data=serializer.errors,
            status=HTTP_400_BAD_REQUEST,
        )

    @extend_schema(
        tags=["Posts"],
        summary="Retrieve a post by slug",
        description=(
            "Returns full post details for the given slug. Authentication is optional. "
            "Side effects: none besides access logging. Language behavior: category name is localized "
            "by active request language. Timezone behavior: `created_at` and `updated_at` are formatted "
            "in authenticated user's timezone or UTC for anonymous requests.\n\n"
            "Request example:\n"
            "GET /api/posts/django-tips/\n\n"
            "Response example (200):\n"
            "{\n"
            "  \"id\": 15,\n"
            "  \"title\": \"Django Tips\",\n"
            "  \"slug\": \"django-tips\",\n"
            "  \"body\": \"Use serializers wisely.\",\n"
            "  \"status\": \"published\"\n"
            "}"
        ),
        responses={
            200: OpenApiResponse(
                response=PostDetailSerializer,
                description="Post details returned successfully.",
            ),
            404: OpenApiResponse(
                response=BlogNotFoundErrorResponse,
                description="Post with provided slug was not found.",
            ),
        },
        examples=[
            OpenApiExample(
                "Retrieve Post Success",
                value={
                    "id": 15,
                    "author": {
                        "id": 7,
                        "email": "alice@example.com",
                        "first_name": "Alice",
                        "last_name": "Smith",
                        "avatar": None,
                    },
                    "title": "Django Tips",
                    "slug": "django-tips",
                    "body": "Use serializers wisely.",
                    "category": {"id": 2, "name": "Backend", "slug": "backend"},
                    "tags": [{"id": 3, "name": "django", "slug": "django"}],
                    "status": "published",
                    "created_at": "14:20 13-03-2026",
                    "updated_at": "14:20 13-03-2026",
                },
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "Retrieve Post Not Found",
                value={"detail": "Post not found"},
                response_only=True,
                status_codes=["404"],
            ),
        ],
    )
    def retrieve(
        self,
        request: DRFRequest,
        slug: str = None,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:

        self.check_permissions(request)

        logger.info(f"Retrieving post with slug={slug}")

        try:
            post: Post = Post.objects.get(slug=slug)
            logger.info(f"Post retrieved: post_id={post.id}, slug={slug}")
        except Post.DoesNotExist:
            logger.warning(f"Post not found: slug={slug}")
            raise NotFound(detail="Post not found")

        serializer: PostDetailSerializer = PostDetailSerializer(
            post, context={"request": request}
        )
        return DRFResponse(
            data=serializer.data,
            status=HTTP_200_OK,
        )

    @extend_schema(
        tags=["Posts"],
        summary="Partially update own post by slug",
        description=(
            "Partially updates an existing post identified by slug. Authentication is required and only "
            "the author can update. Side effects: invalidates cache key `published_posts_list` on success. "
            "Language behavior: validation errors may be localized. Timezone behavior: datetime fields in "
            "response follow serializer formatting rules.\n\n"
            "Request example:\n"
            "PATCH /api/posts/django-tips/\n"
            "Authorization: Bearer <jwt-access-token>\n"
            "{\n"
            "  \"status\": \"published\"\n"
            "}\n\n"
            "Response example (200):\n"
            "{\n"
            "  \"id\": 15,\n"
            "  \"status\": \"published\"\n"
            "}"
        ),
        request=PostCreateUpdateSerializer,
        responses={
            200: OpenApiResponse(
                response=PostCreateUpdateSerializer,
                description="Post updated successfully.",
            ),
            400: OpenApiResponse(
                response=BlogValidationErrorResponse,
                description="Invalid patch payload.",
            ),
            401: OpenApiResponse(
                response=BlogUnauthorizedErrorResponse,
                description="Authentication required.",
            ),
            403: OpenApiResponse(
                response=BlogForbiddenErrorResponse,
                description="Authenticated user is not the post author.",
            ),
            404: OpenApiResponse(
                response=BlogNotFoundErrorResponse,
                description="Post with provided slug was not found.",
            ),
        },
        examples=[
            OpenApiExample(
                "Patch Post Request",
                value={"status": "published"},
                request_only=True,
            ),
            OpenApiExample(
                "Patch Post Success",
                value={
                    "id": 15,
                    "title": "Django Tips",
                    "slug": "django-tips",
                    "status": "published",
                },
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "Patch Post Forbidden",
                value={"detail": "You do not have permission to perform this action."},
                response_only=True,
                status_codes=["403"],
            ),
        ],
    )
    def partial_update(
        self,
        request: DRFRequest,
        slug: str = None,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:

        self.check_permissions(request)

        if not request.user.is_authenticated:
            logger.warning(f"Unauthorized attempt to update post with slug={slug}")
            return DRFResponse(
                data={"detail": "Authentication required."},
                status=HTTP_401_UNAUTHORIZED,
            )

        logger.info(f"Updating post: slug={slug}, user_id={request.user.id}")

        try:
            post: Post = Post.objects.get(slug=slug)
        except Post.DoesNotExist:
            logger.warning(f"Post not found for update: slug={slug}")
            raise NotFound(detail="Post not found")

        self.check_object_permissions(request, post)

        serializer: PostCreateUpdateSerializer = PostCreateUpdateSerializer(
            post,
            data=request.data,
            partial=True,
        )

        if serializer.is_valid():
            serializer.save()

            cache.delete("published_posts_list")
            logger.info("Invalidated published posts cache after post update")

            logger.info(
                f"Post updated successfully: post_id={post.id}, "
                f"slug={slug}, user_id={request.user.id}"
            )
            return DRFResponse(
                data=serializer.data,
                status=HTTP_200_OK,
            )

        logger.error(
            f"Post update failed: post_id={post.id}, "
            f"user_id={request.user.id}, errors={serializer.errors}"
        )
        return DRFResponse(
            data=serializer.errors,
            status=HTTP_400_BAD_REQUEST,
        )

    @extend_schema(
        tags=["Posts"],
        summary="Delete own post by slug",
        description=(
            "Deletes a post identified by slug. Authentication is required and only the author can delete. "
            "Side effects: permanently deletes post record. Language/timezone behavior: not applicable for "
            "successful 204 response body-less output.\n\n"
            "Request example:\n"
            "DELETE /api/posts/django-tips/\n"
            "Authorization: Bearer <jwt-access-token>\n\n"
            "Response example (204): no content"
        ),
        responses={
            204: OpenApiResponse(description="Post deleted successfully."),
            401: OpenApiResponse(
                response=BlogUnauthorizedErrorResponse,
                description="Authentication required.",
            ),
            403: OpenApiResponse(
                response=BlogForbiddenErrorResponse,
                description="Authenticated user is not the post author.",
            ),
            404: OpenApiResponse(
                response=BlogNotFoundErrorResponse,
                description="Post with provided slug was not found.",
            ),
        },
        examples=[
            OpenApiExample(
                "Delete Post Forbidden",
                value={"detail": "You do not have permission to perform this action."},
                response_only=True,
                status_codes=["403"],
            ),
            OpenApiExample(
                "Delete Post Not Found",
                value={"detail": "Post not found"},
                response_only=True,
                status_codes=["404"],
            ),
        ],
    )
    def destroy(
        self,
        request: DRFRequest,
        slug: str = None,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:

        self.check_permissions(request)

        if not request.user.is_authenticated:
            logger.warning(f"Unauthorized attempt to delete post with slug={slug}")
            return DRFResponse(
                data={"detail": "Authentication required."},
                status=HTTP_401_UNAUTHORIZED,
            )

        logger.info(f"Deleting post: slug={slug}, user_id={request.user.id}")

        try:
            post: Post = Post.objects.get(slug=slug)
        except Post.DoesNotExist:
            logger.warning(f"Post not found for deletion: slug={slug}")
            raise NotFound(detail="Post not found")

        self.check_object_permissions(request, post)

        post_id = post.id
        post.delete()
        logger.info(
            f"Post deleted successfully: post_id={post_id}, "
            f"slug={slug}, user_id={request.user.id}"
        )
        return DRFResponse(status=HTTP_204_NO_CONTENT)
    
    @action(
        detail=True,
        methods=("GET", "POST"),
        url_path="comments",
        url_name="comments",
        permission_classes=(AllowAny,),
    )
    @extend_schema(
        tags=["Comments"],
        summary="List comments for a post or add a new comment",
        description=(
            "GET returns comments for a post by slug (authentication optional). POST creates a new comment "
            "for that post (authentication required). Side effects: on successful POST, publishes a Redis "
            "event to channel `comments`. Language behavior: validation errors/messages may be localized. "
            "Timezone behavior: comment timestamps are formatted in the authenticated user's timezone or UTC "
            "for anonymous GET requests.\n\n"
            "GET request example:\n"
            "GET /api/posts/django-tips/comments/\n\n"
            "POST request example:\n"
            "POST /api/posts/django-tips/comments/\n"
            "Authorization: Bearer <jwt-access-token>\n"
            "{\n"
            "  \"body\": \"Great article!\"\n"
            "}"
        ),
        request=CommentSerializer,
        responses={
            200: OpenApiResponse(
                response=CommentSerializer(many=True),
                description="Comments listed successfully (GET).",
            ),
            201: OpenApiResponse(
                response=CommentSerializer,
                description="Comment created successfully (POST).",
            ),
            400: OpenApiResponse(
                response=BlogValidationErrorResponse,
                description="Invalid comment payload.",
            ),
            401: OpenApiResponse(
                response=BlogUnauthorizedErrorResponse,
                description="Authentication required to create a comment.",
            ),
            404: OpenApiResponse(
                response=BlogNotFoundErrorResponse,
                description="Post with provided slug was not found.",
            ),
        },
        examples=[
            OpenApiExample(
                "Create Comment Request",
                value={"body": "Great article!"},
                request_only=True,
            ),
            OpenApiExample(
                "List Comments Success",
                value={
                    "next": None,
                    "previous": None,
                    "results": [
                        {
                            "id": 33,
                            "author": {
                                "id": 7,
                                "email": "alice@example.com",
                                "first_name": "Alice",
                                "last_name": "Smith",
                                "avatar": None,
                            },
                            "body": "Great article!",
                            "created_at": "16:30 13-03-2026",
                            "updated_at": "16:30 13-03-2026",
                        }
                    ],
                },
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "Create Comment Success",
                value={
                    "id": 33,
                    "author": {
                        "id": 7,
                        "email": "alice@example.com",
                        "first_name": "Alice",
                        "last_name": "Smith",
                        "avatar": None,
                    },
                    "body": "Great article!",
                    "created_at": "16:30 13-03-2026",
                    "updated_at": "16:30 13-03-2026",
                },
                response_only=True,
                status_codes=["201"],
            ),
        ],
    )
    def comments(
        self,
        request: DRFRequest,
        slug: str = None,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        logger.info(f"Comments action: method={request.method}, slug={slug}")

        try:
            post: Post = Post.objects.get(slug=slug)
        except Post.DoesNotExist:
            logger.warning(f"Post not found for comments: slug={slug}")
            raise NotFound(detail="Post not found")

        if request.method == "GET":
            logger.info(f"Listing comments for post: post_id={post.id}, slug={slug}")
            comments_qs = post.comments.all().order_by("-created_at")

            paginator = self.pagination_class()
            page = paginator.paginate_queryset(comments_qs, request, view=self)

            if page is not None:
                serializer: CommentSerializer = CommentSerializer(
                    page, many=True, context={"request": request}
                )
                return paginator.get_paginated_response(serializer.data)

            serializer: CommentSerializer = CommentSerializer(
                comments_qs, many=True, context={"request": request}
            )
            return DRFResponse(
                data=serializer.data,
                status=HTTP_200_OK,
            )

        elif request.method == "POST":
            if not request.user.is_authenticated:
                logger.warning(
                    f"Unauthorized attempt to comment on post: post_id={post.id}"
                )
                return DRFResponse(
                    data={"detail": "Authentication required to post comments."},
                    status=HTTP_401_UNAUTHORIZED,
                )

            logger.info(
                f"Creating comment: post_id={post.id}, user_id={request.user.id}"
            )

            serializer: CommentSerializer = CommentSerializer(
                data=request.data, context={"request": request}
            )
            if serializer.is_valid():
                comment = serializer.save(author=request.user, post=post)
                logger.info(
                    f"Comment created successfully: comment_id={comment.id}, "
                    f"post_id={post.id}, user_id={request.user.id}"
                )
                return DRFResponse(
                    data=serializer.data,
                    status=HTTP_201_CREATED,
                )

            logger.error(
                f"Comment creation failed: post_id={post.id}, "
                f"user_id={request.user.id}, errors={serializer.errors}"
            )
            return DRFResponse(
                data=serializer.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class CommentViewSet(ViewSet):
    permission_classes: tuple = (IsAuthorOrReadOnly,)
    pagination_class = DefaultPagination
    serializer_class = CommentSerializer

    def get_serializer_class(self):
        return self.serializer_class

    def get_permissions(self):
        return [permission() for permission in self.permission_classes]

    def check_permissions(self, request):
        for permission in self.get_permissions():
            if not permission.has_permission(request, self):
                raise PermissionDenied()

    def check_object_permissions(self, request, obj):
        for permission in self.get_permissions():
            if not permission.has_object_permission(request, self, obj):
                raise PermissionDenied()

    @extend_schema(
        tags=["Comments", "Stats"],
        summary="List all comments",
        description=(
            "Returns a paginated list of all comments ordered by newest first. Authentication is optional. "
            "Side effects: none. Language behavior: none for body text, but translated errors can appear for "
            "other methods in this viewset. Timezone behavior: timestamp fields are formatted in authenticated "
            "user timezone or UTC for anonymous requests.\n\n"
            "Request example:\n"
            "GET /api/comments/?cursor=<cursor>&page_size=10\n\n"
            "Response example (200):\n"
            "{\n"
            "  \"next\": null,\n"
            "  \"previous\": null,\n"
            "  \"results\": [\n"
            "    {\n"
            "      \"id\": 33,\n"
            "      \"body\": \"Great article!\"\n"
            "    }\n"
            "  ]\n"
            "}"
        ),
        responses={
            200: OpenApiResponse(
                response=CommentSerializer(many=True),
                description="Comments listed successfully (typically paginated).",
            )
        },
        examples=[
            OpenApiExample(
                "Comment List Success",
                value={
                    "next": None,
                    "previous": None,
                    "results": [
                        {
                            "id": 33,
                            "author": {
                                "id": 7,
                                "email": "alice@example.com",
                                "first_name": "Alice",
                                "last_name": "Smith",
                                "avatar": None,
                            },
                            "body": "Great article!",
                            "created_at": "16:30 13-03-2026",
                            "updated_at": "16:30 13-03-2026",
                        }
                    ],
                },
                response_only=True,
                status_codes=["200"],
            )
        ],
    )
    def list(
        self,
        request: DRFRequest,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        self.check_permissions(request)

        logger.info("Listing all comments")
        queryset = Comment.objects.all().order_by("-created_at")
        logger.debug(f"Total comments count: {queryset.count()}")

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)

        if page is not None:
            serializer: CommentSerializer = CommentSerializer(
                page, many=True, context={"request": request}
            )
            return paginator.get_paginated_response(serializer.data)

        serializer: CommentSerializer = CommentSerializer(
            queryset, many=True, context={"request": request}
        )
        return DRFResponse(
            data=serializer.data,
            status=HTTP_200_OK,
        )

    @extend_schema(
        tags=["Comments"],
        summary="Retrieve a comment by id",
        description=(
            "Returns a single comment by primary key. Authentication is optional. Side effects: none. "
            "Language behavior: not applicable for comment content. Timezone behavior: timestamp fields are "
            "formatted by authenticated user timezone or UTC for anonymous requests.\n\n"
            "Request example:\n"
            "GET /api/comments/33/\n\n"
            "Response example (200):\n"
            "{\n"
            "  \"id\": 33,\n"
            "  \"body\": \"Great article!\"\n"
            "}"
        ),
        responses={
            200: OpenApiResponse(
                response=CommentSerializer,
                description="Comment returned successfully.",
            ),
            404: OpenApiResponse(
                response=BlogNotFoundErrorResponse,
                description="Comment with provided id was not found.",
            ),
        },
        examples=[
            OpenApiExample(
                "Retrieve Comment Success",
                value={
                    "id": 33,
                    "author": {
                        "id": 7,
                        "email": "alice@example.com",
                        "first_name": "Alice",
                        "last_name": "Smith",
                        "avatar": None,
                    },
                    "body": "Great article!",
                    "created_at": "16:30 13-03-2026",
                    "updated_at": "16:30 13-03-2026",
                },
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "Retrieve Comment Not Found",
                value={"detail": "Comment not found"},
                response_only=True,
                status_codes=["404"],
            ),
        ],
    )
    def retrieve(
        self,
        request: DRFRequest,
        pk: int = None,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        self.check_permissions(request)

        logger.info(f"Retrieving comment with pk={pk}")

        try:
            comment: Comment = Comment.objects.get(pk=pk)
            logger.info(f"Comment retrieved: comment_id={comment.id}")
        except Comment.DoesNotExist:
            logger.warning(f"Comment not found: pk={pk}")
            raise NotFound(detail="Comment not found")

        serializer: CommentSerializer = CommentSerializer(
            comment, context={"request": request}
        )
        return DRFResponse(
            data=serializer.data,
            status=HTTP_200_OK,
        )

    @extend_schema(
        tags=["Comments"],
        summary="Partially update own comment",
        description=(
            "Partially updates an existing comment by id. Authentication is required and only the comment "
            "author can update. Side effects: updates persisted comment data. Language behavior: validation "
            "errors may be localized. Timezone behavior: updated timestamps are formatted by serializer rules.\n\n"
            "Request example:\n"
            "PATCH /api/comments/33/\n"
            "Authorization: Bearer <jwt-access-token>\n"
            "{\n"
            "  \"body\": \"Updated text\"\n"
            "}\n\n"
            "Response example (200):\n"
            "{\n"
            "  \"id\": 33,\n"
            "  \"body\": \"Updated text\"\n"
            "}"
        ),
        request=CommentSerializer,
        responses={
            200: OpenApiResponse(
                response=CommentSerializer,
                description="Comment updated successfully.",
            ),
            400: OpenApiResponse(
                response=BlogValidationErrorResponse,
                description="Invalid comment patch payload.",
            ),
            401: OpenApiResponse(
                response=BlogUnauthorizedErrorResponse,
                description="Authentication required.",
            ),
            403: OpenApiResponse(
                response=BlogForbiddenErrorResponse,
                description="Authenticated user is not the comment author.",
            ),
            404: OpenApiResponse(
                response=BlogNotFoundErrorResponse,
                description="Comment with provided id was not found.",
            ),
        },
        examples=[
            OpenApiExample(
                "Patch Comment Request",
                value={"body": "Updated text"},
                request_only=True,
            ),
            OpenApiExample(
                "Patch Comment Success",
                value={
                    "id": 33,
                    "author": {
                        "id": 7,
                        "email": "alice@example.com",
                        "first_name": "Alice",
                        "last_name": "Smith",
                        "avatar": None,
                    },
                    "body": "Updated text",
                    "created_at": "16:30 13-03-2026",
                    "updated_at": "16:45 13-03-2026",
                },
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "Patch Comment Forbidden",
                value={"detail": "You do not have permission to perform this action."},
                response_only=True,
                status_codes=["403"],
            ),
        ],
    )
    def partial_update(
        self,
        request: DRFRequest,
        pk: int = None,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        self.check_permissions(request)

        if not request.user.is_authenticated:
            logger.warning(f"Unauthorized attempt to update comment with pk={pk}")
            return DRFResponse(
                data={"detail": "Authentication required."},
                status=HTTP_401_UNAUTHORIZED,
            )

        logger.info(f"Updating comment: pk={pk}, user_id={request.user.id}")

        try:
            comment: Comment = Comment.objects.get(pk=pk)
        except Comment.DoesNotExist:
            logger.warning(f"Comment not found for update: pk={pk}")
            raise NotFound(detail="Comment not found")

        self.check_object_permissions(request, comment)

        serializer: CommentSerializer = CommentSerializer(
            comment,
            data=request.data,
            partial=True,
            context={"request": request},
        )

        if serializer.is_valid():
            serializer.save()
            logger.info(
                f"Comment updated successfully: comment_id={comment.id}, "
                f"user_id={request.user.id}"
            )
            return DRFResponse(
                data=serializer.data,
                status=HTTP_200_OK,
            )

        logger.error(
            f"Comment update failed: comment_id={comment.id}, "
            f"user_id={request.user.id}, errors={serializer.errors}"
        )
        return DRFResponse(
            data=serializer.errors,
            status=HTTP_400_BAD_REQUEST,
        )

    @extend_schema(
        tags=["Comments"],
        summary="Delete own comment",
        description=(
            "Deletes a comment by id. Authentication is required and only the comment author can delete. "
            "Side effects: permanently deletes the comment. Language/timezone behavior: not applicable for "
            "204 no-content success response.\n\n"
            "Request example:\n"
            "DELETE /api/comments/33/\n"
            "Authorization: Bearer <jwt-access-token>\n\n"
            "Response example (204): no content"
        ),
        responses={
            204: OpenApiResponse(description="Comment deleted successfully."),
            401: OpenApiResponse(
                response=BlogUnauthorizedErrorResponse,
                description="Authentication required.",
            ),
            403: OpenApiResponse(
                response=BlogForbiddenErrorResponse,
                description="Authenticated user is not the comment author.",
            ),
            404: OpenApiResponse(
                response=BlogNotFoundErrorResponse,
                description="Comment with provided id was not found.",
            ),
        },
        examples=[
            OpenApiExample(
                "Delete Comment Forbidden",
                value={"detail": "You do not have permission to perform this action."},
                response_only=True,
                status_codes=["403"],
            ),
            OpenApiExample(
                "Delete Comment Not Found",
                value={"detail": "Comment not found"},
                response_only=True,
                status_codes=["404"],
            ),
        ],
    )
    def destroy(
        self,
        request: DRFRequest,
        pk: int = None,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        self.check_permissions(request)

        if not request.user.is_authenticated:
            logger.warning(f"Unauthorized attempt to delete comment with pk={pk}")
            return DRFResponse(
                data={"detail": "Authentication required."},
                status=HTTP_401_UNAUTHORIZED,
            )

        logger.info(f"Deleting comment: pk={pk}, user_id={request.user.id}")

        try:
            comment: Comment = Comment.objects.get(pk=pk)
        except Comment.DoesNotExist:
            logger.warning(f"Comment not found for deletion: pk={pk}")
            raise NotFound(detail="Comment not found")

        self.check_object_permissions(request, comment)

        comment_id = comment.id
        comment.delete()
        logger.info(
            f"Comment deleted successfully: comment_id={comment_id}, "
            f"user_id={request.user.id}"
        )
        return DRFResponse(status=HTTP_204_NO_CONTENT)


class StatsView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        tags=["Stats"],
        summary="Get public stats snapshot",
        description=(
            "Returns external exchange rates and current Almaty time. "
            "The endpoint fetches both external APIs concurrently for lower latency."
        ),
        responses={
            200: inline_serializer(
                name="StatsResponse",
                fields={
                    "exchange_rates": serializers.DictField(),
                    "almaty_time": serializers.CharField(),
                    "timezone": serializers.CharField(),
                    "time_source": serializers.CharField(),
                },
            ),
            503: inline_serializer(
                name="StatsErrorResponse",
                fields={
                    "detail": serializers.CharField(),
                },
            ),
        },
    )
    def get(self, request: DRFRequest, *args: tuple[Any, ...], **kwargs: dict[str, Any]) -> DRFResponse:
        try:
            payload = async_to_sync(self._fetch_stats_snapshot)()
            return DRFResponse(data=payload, status=HTTP_200_OK)
        except (httpx.HTTPError, ValueError) as exc:
            logger.error(f"Failed to fetch stats snapshot: {exc}", exc_info=True)
            return DRFResponse(
                data={"detail": "Failed to fetch external stats providers."},
                status=HTTP_503_SERVICE_UNAVAILABLE,
            )

    async def _fetch_stats_snapshot(self) -> dict[str, Any]:
        # Async is used to run both outbound HTTP calls concurrently; synchronous requests would wait for each provider one by one.
        exchange_url = "https://open.er-api.com/v6/latest/USD"
        almaty_time_urls = (
            "https://worldtimeapi.org/api/timezone/Asia/Almaty",
            "http://worldtimeapi.org/api/timezone/Asia/Almaty",
        )

        async def fetch_almaty_time(client: httpx.AsyncClient) -> dict[str, str]:
            last_exc: Exception | None = None
            for url in almaty_time_urls:
                try:
                    response = await client.get(url)
                    response.raise_for_status()
                    payload = response.json()
                    return {
                        "almaty_time": payload.get("datetime") or "",
                        "timezone": payload.get("timezone", "Asia/Almaty"),
                        "time_source": "worldtimeapi.org",
                    }
                except httpx.HTTPError as exc:
                    last_exc = exc

            if last_exc is not None:
                logger.warning(
                    "worldtimeapi.org is unavailable, falling back to local Asia/Almaty time: %s",
                    last_exc,
                )

            fallback_dt = datetime.now(ZoneInfo("Asia/Almaty")).isoformat()
            return {
                "almaty_time": fallback_dt,
                "timezone": "Asia/Almaty",
                "time_source": "local_fallback",
            }

        async with httpx.AsyncClient(timeout=10.0) as client:
            exchange_response, time_payload = await asyncio.gather(
                client.get(exchange_url),
                fetch_almaty_time(client),
            )

        exchange_response.raise_for_status()

        exchange_payload = exchange_response.json()
        rates = exchange_payload.get("rates", {})

        return {
            "exchange_rates": {
                "KZT": rates.get("KZT"),
                "RUB": rates.get("RUB"),
                "EUR": rates.get("EUR"),
            },
            "almaty_time": time_payload.get("almaty_time"),
            "timezone": time_payload.get("timezone", "Asia/Almaty"),
            "time_source": time_payload.get("time_source", "worldtimeapi.org"),
        }
