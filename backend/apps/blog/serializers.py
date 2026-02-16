# Python modules
from datetime import datetime
import logging

# Third-party modules
from rest_framework.serializers import (
    ModelSerializer,
    DateTimeField,
    SlugField,
    PrimaryKeyRelatedField,
)

# Project modules
from apps.blog.models import Post, Category, Tag, Comment
from apps.users.models import CustomUser

logger = logging.getLogger(__name__)


class AuthorSerializer(ModelSerializer):
    """
    Base Author serializer
    """

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "avatar",
        ]


class CategorySerializer(ModelSerializer):
    """
    Base Category Serializer
    """

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
        ]


class TagSerializer(ModelSerializer):
    """
    Base Tag Serializer
    """

    class Meta:
        model = Tag
        fields = [
            "id",
            "name",
            "slug",
        ]


class PostListSerializer(ModelSerializer):
    """
    Post GET List serializer
    """

    author: AuthorSerializer = AuthorSerializer(read_only=True)
    category: CategorySerializer = CategorySerializer(read_only=True)
    tags: TagSerializer = TagSerializer(read_only=True, many=True)

    created_at: datetime = DateTimeField(read_only=True, format="%H:%M %d-%m-%Y")

    class Meta:
        model = Post
        fields = [
            "id",
            "author",
            "title",
            "slug",
            "category",
            "tags",
            "status",
            "created_at",
        ]

    def to_representation(self, instance):
        logger.debug(f"Serializing post list item: post_id={instance.id}, slug={instance.slug}")
        return super().to_representation(instance)


class PostDetailSerializer(ModelSerializer):
    """
    Post GET by ID serializer
    """

    author: AuthorSerializer = AuthorSerializer(read_only=True)
    category: CategorySerializer = CategorySerializer(read_only=True)
    tags: TagSerializer = TagSerializer(read_only=True, many=True)

    created_at: datetime = DateTimeField(
        read_only=True,
        format="%H:%M %d-%m-%Y",
    )
    updated_at: datetime = DateTimeField(
        read_only=True,
        format="%H:%M %d-%m-%Y",
    )

    class Meta:
        model = Post
        fields = [
            "id",
            "author",
            "title",
            "slug",
            "body",
            "category",
            "tags",
            "status",
            "created_at",
            "updated_at",
        ]

    def to_representation(self, instance):
        logger.debug(f"Serializing post detail: post_id={instance.id}, slug={instance.slug}")
        return super().to_representation(instance)


class PostCreateUpdateSerializer(ModelSerializer):
    """
    Post POST and PUT, PATCH Serializer
    """

    author = AuthorSerializer(read_only=True)
    slug = SlugField(read_only=True)
    category = PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        required=False,
        allow_null=True,
    )
    tags = PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=False,
    )

    class Meta:
        model = Post
        fields = [
            "id",
            "author",
            "title",
            "slug",
            "body",
            "category",
            "tags",
            "status",
        ]

    def validate(self, attrs):
        logger.debug(f"Validating post data: title={attrs.get('title', 'N/A')}")
        return super().validate(attrs)

    def create(self, validated_data):
        logger.info(f"Creating post via serializer: title={validated_data.get('title')}")
        post = super().create(validated_data)
        logger.debug(f"Post created in serializer: post_id={post.id}, slug={post.slug}")
        return post

    def update(self, instance, validated_data):
        logger.info(f"Updating post via serializer: post_id={instance.id}, title={validated_data.get('title', instance.title)}")
        post = super().update(instance, validated_data)
        logger.debug(f"Post updated in serializer: post_id={post.id}")
        return post


class CommentSerializer(ModelSerializer):
    author: AuthorSerializer = AuthorSerializer(read_only=True)

    created_at = DateTimeField(read_only=True, format="%H:%M %d-%m-%Y")
    updated_at = DateTimeField(read_only=True, format="%H:%M %d-%m-%Y")

    class Meta:
        model = Comment
        fields = [
            "id",
            "author",
            "body",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        logger.debug(f"Validating comment data: body_length={len(attrs.get('body', ''))}")
        return super().validate(attrs)

    def create(self, validated_data):
        logger.info("Creating comment via serializer")
        comment = super().create(validated_data)
        logger.debug(f"Comment created in serializer: comment_id={comment.id}")
        return comment

    def update(self, instance, validated_data):
        logger.info(f"Updating comment via serializer: comment_id={instance.id}")
        comment = super().update(instance, validated_data)
        logger.debug(f"Comment updated in serializer: comment_id={comment.id}")
        return comment

    def to_representation(self, instance):
        logger.debug(f"Serializing comment: comment_id={instance.id}")
        return super().to_representation(instance)
