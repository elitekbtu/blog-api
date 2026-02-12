# Python modules
from typing import Any

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
        fields = ["email", "password", "password_confirm", "tokens"]

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs["password"] != attrs["password_confirm"]:
            raise ValidationError({"password": "Passwords must match!"})
        return attrs

    def create(self, validated_data: dict[str, Any]) -> CustomUser:
        validated_data.pop("password_confirm")
        user = CustomUser.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
        )
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

        user = authenticate(
            request=self.context.get("request"), email=email, password=password
        )

        if not user:
            raise ValidationError("Invalid email or password")

        refresh = RefreshToken.for_user(user)

        return {
            "email": user.email,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }
