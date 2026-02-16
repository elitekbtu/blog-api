# Python modules
from typing import Any
import logging

# Third-party modules
from rest_framework.serializers import (
    CharField,
    EmailField,
    SerializerMethodField,
    Serializer,
    ModelSerializer,
    ValidationError,
)
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

# Project modules
from apps.users.models import CustomUser

logger = logging.getLogger(__name__)


class RegistrationSerializer(ModelSerializer):
    """
    Registration serializer for CustomUser model

    Fields:
        - email: Email of the user
        - password: Password of the user
        - password_confirm: Password confirmation
        - tokens: JWT tokens for the user (access and refresh)
    Methods:
        - validate: Validate the password and password confirmation
        - create: Create a new user instance
        - get_tokens: Get JWT tokens for the user
    """

    password = CharField(
        min_length=8,
        write_only=True,
    )
    password_confirm = CharField(
        min_length=8,
        write_only=True,
    )

    tokens = SerializerMethodField(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "email",
            "first_name",
            "last_name",
            "password",
            "password_confirm",
            "tokens",
        ]

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        email = attrs.get("email", "N/A")
        logger.debug(f"Validating registration data for email={email}")
        if attrs["password"] != attrs["password_confirm"]:
            logger.warning(f"Password mismatch during registration: email={email}")
            raise ValidationError({"password": "Passwords must match!"})
        logger.debug(f"Registration validation successful: email={email}")
        return attrs

    def create(self, validated_data: dict[str, Any]) -> CustomUser:
        email = validated_data.get("email")
        logger.info(f"Creating new user: email={email}")
        validated_data.pop("password_confirm")
        user = CustomUser.objects.create_user(**validated_data)
        logger.info(f"User created successfully: user_id={user.id}, email={email}")
        return user

    def get_tokens(self, obj: CustomUser) -> dict[str, str]:
        refresh = RefreshToken.for_user(obj)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }


class LoginSerializer(Serializer):
    """
    Login serializer for CustomUser model

    Fields:
        - email: Email of the user
        - password: Password of the user
        - access: Access token for the user
        - refresh: Refresh token for the user
    Methods:
        - validate: Validate the email and password and return tokens
    """

    email = EmailField()
    password = CharField(write_only=True)

    access = CharField(read_only=True)
    refresh = CharField(read_only=True)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        email = attrs.get("email")
        password = attrs.get("password")

        logger.debug(f"Authenticating user: email={email}")
        user = authenticate(
            request=self.context.get("request"), email=email, password=password
        )

        if not user:
            logger.warning(f"Authentication failed: email={email}")
            raise ValidationError("Invalid email or password")

        logger.info(f"Authentication successful: user_id={user.id}, email={email}")
        refresh = RefreshToken.for_user(user)
        logger.debug(f"Generated tokens for user_id={user.id}")

        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }
