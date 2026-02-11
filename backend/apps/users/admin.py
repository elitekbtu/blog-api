# Django modules
from django.contrib import admin
from django.contrib.admin import ModelAdmin

# Project modules
from apps.users.models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(ModelAdmin):
    """Admin interface for CustomUser model"""

    list_display = (
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_active",
        "is_superuser",
        "date_joined",
        "created_at",
        "updated_at",
        "deleted_at",
    )
    search_fields = ("email", "first_name", "last_name")
    list_filter = ("is_staff", "is_active", "is_superuser")
