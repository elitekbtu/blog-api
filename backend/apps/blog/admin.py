# Django modules
from django.contrib import admin
from django.contrib.admin import ModelAdmin

# Project modules
from apps.blog.models import Category, Tag, Post, Comment


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    """Admin interface for Category model"""

    list_display = (
        "name",
        "slug",
        "created_at",
        "updated_at",
        "deleted_at",
    )

    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("-created_at",)


@admin.register(Tag)
class TagAdmin(ModelAdmin):
    """Admin interface for Tag model"""

    list_display = (
        "name",
        "slug",
        "created_at",
        "updated_at",
        "deleted_at",
    )

    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("-created_at",)


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

    search_fields = (
        "title",
        "body",
        "author__email",  # или author__username если нужно
        "category__name",
    )

    list_filter = (
        "status",
        "category",
        "author",
        "created_at",
    )

    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("tags",)

    list_select_related = ("author", "category")
    ordering = ("-created_at",)

    readonly_fields = ("created_at", "updated_at")


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

    search_fields = (
        "body",
        "author__email",
        "post__title",
    )

    list_filter = (
        "post",
        "author",
        "created_at",
    )

    list_select_related = ("post", "author")
    ordering = ("-created_at",)

    readonly_fields = ("created_at", "updated_at")
