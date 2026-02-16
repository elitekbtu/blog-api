# Python modules
from typing import Any
import logging

# Third-party modules
from rest_framework.viewsets import ViewSet
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
)
from rest_framework.exceptions import NotFound, PermissionDenied

# Django modules
from django.db.models import Q

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

logger = logging.getLogger(__name__)


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

        if not request.user.is_authenticated:
            queryset = Post.objects.filter(status=Post.Status.PUBLISHED)
        else:
            queryset = Post.objects.filter(
                Q(status=Post.Status.PUBLISHED) | Q(author=request.user)
            )

        logger.debug(f"Posts queryset count: {queryset.count()} for {user_info}")

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)

        if page is not None:
            serializer: PostListSerializer = PostListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer: PostListSerializer = PostListSerializer(queryset, many=True)
        return DRFResponse(
            data=serializer.data,
            status=HTTP_200_OK,
        )

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

        serializer: PostDetailSerializer = PostDetailSerializer(post)
        return DRFResponse(
            data=serializer.data,
            status=HTTP_200_OK,
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
                serializer: CommentSerializer = CommentSerializer(page, many=True)
                return paginator.get_paginated_response(serializer.data)

            serializer: CommentSerializer = CommentSerializer(comments_qs, many=True)
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

            serializer: CommentSerializer = CommentSerializer(data=request.data)
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
            serializer: CommentSerializer = CommentSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer: CommentSerializer = CommentSerializer(queryset, many=True)
        return DRFResponse(
            data=serializer.data,
            status=HTTP_200_OK,
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

        serializer: CommentSerializer = CommentSerializer(comment)
        return DRFResponse(
            data=serializer.data,
            status=HTTP_200_OK,
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
