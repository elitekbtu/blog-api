# Python modules
import logging

# Django modules
from django.utils.translation import gettext_lazy as _

# Third-party modules
from rest_framework.serializers import ModelSerializer, DateTimeField, ValidationError

# Project modules
from apps.users.models import CustomUser
from utils.datetime_helper import format_user_datetime
from utils.timezone_validator import TimezoneValidator

logger = logging.getLogger(__name__)


class CustomUserSerializer(ModelSerializer):
    """
    Base Serializer for CustomUser
    """

    date_joined: DateTimeField = DateTimeField(
        read_only=True,
        format="%H:%M %d-%m-%Y",
    )

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "avatar",
            "date_joined",
        ]

    def to_representation(self, instance):
        logger.debug(f"Serializing user: user_id={instance.id}, email={instance.email}")

        data = super().to_representation(instance)

        request = self.context.get("request")
        user = request.user if request else None

        if instance.date_joined:
            data["date_joined"] = format_user_datetime(instance.date_joined, user)

        return data


class UserPreferencesSerializer(ModelSerializer):

    class Meta:
        model = CustomUser
        fields = ["preferred_language", "timezone"]

    def validate_preferred_language(self, value):

        supported = dict(CustomUser.LANGUAGE_CHOICES)

        if value not in supported:
            raise ValidationError(
                _("Unsupported language.")
            )

        return value

    def validate_timezone(self, value):
        TimezoneValidator()(value)
        return value
