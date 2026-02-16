# Python modules
import logging

# Third-party modules
from rest_framework.serializers import ModelSerializer, DateTimeField

# Project modules
from apps.users.models import CustomUser

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
        return super().to_representation(instance)
