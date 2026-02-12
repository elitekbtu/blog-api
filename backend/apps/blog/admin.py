# Django modules
from django.contrib import admin
from django.contrib.admin import ModelAdmin

# Project modules
from apps.blog.models import Category, Tag, Post, Comment


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    """Admin interface for Category model"""

    list_display = ("name", "slug", "created_at", "updated_at", "deleted_at")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Tag)
class TagAdmin(ModelAdmin):
    """Admin interface for Tag model"""

    list_display = ("name", "slug", "created_at", "updated_at", "deleted_at")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Post)
class PostAdmin(ModelAdmin):
    """Admin interface for Post model"""

    list_display = (
        "title",
        "author",
        "category",
        "status",
        "created_at",
        "updated_at",
        "deleted_at",
    )
    search_fields = ("title", "body")
    list_filter = ("status", "category", "author")


@admin.register(Comment)
class CommentAdmin(ModelAdmin):
    """Admin interface for Comment model"""

    list_display = (
        "post",
        "author",
        "created_at",
        "updated_at",
        "deleted_at",
    )
    search_fields = ("body",)
    list_filter = ("post", "author")
