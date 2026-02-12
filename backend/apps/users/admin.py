# Django modules
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

# Project modules
from apps.users.models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Admin interface for CustomUser model"""

    model = CustomUser

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
    )

    list_filter = (
        "is_staff",
        "is_active",
        "is_superuser",
        "date_joined",
    )

    search_fields = (
        "email",
        "first_name",
        "last_name",
    )

    ordering = ("-date_joined",)

    readonly_fields = (
        "date_joined",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        ("Authentication", {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "avatar")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Important dates",
            {
                "fields": (
                    "date_joined",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )
