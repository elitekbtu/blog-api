# Python modules
from datetime import datetime

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
