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
from apps.blog.models import Post, Category, Tag
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


class PostGetSerializer(ModelSerializer):
    """
    Post GET serializer
    """

    author: AuthorSerializer = AuthorSerializer(read_only=True)
    category: CategorySerializer = CategorySerializer(read_only=True)
    tags: TagSerializer = TagSerializer(read_only=True, many=True)

    created_at: datetime = DateTimeField(read_only=True, format="%H:%M %d-%m-%Y")
    updated_at: datetime = DateTimeField(read_only=True, format="%H:%M %d-%m-%Y")

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
    Post POST/PUT Serializer
    """

    author: int = PrimaryKeyRelatedField(read_only=True)
    slug: str = SlugField(read_only=True)
    created_at: datetime = DateTimeField(read_only=True, format="%H:%M %d-%m-%Y")

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
        ]
