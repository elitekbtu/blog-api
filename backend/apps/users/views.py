# Python modules
from typing import Any
import logging

# Third-party modules
from rest_framework.viewsets import ViewSet
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response as DRFResponse
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    inline_serializer,
)

# Django modules
from django.utils.translation import gettext_lazy as _

# Project modules
from apps.users.serializers import CustomUserSerializer, UserPreferencesSerializer

logger = logging.getLogger(__name__)

UsersUnauthorizedErrorResponse = inline_serializer(
    name="UsersUnauthorizedErrorResponse",
    fields={
        "detail": serializers.CharField(),
    },
)

UsersValidationErrorResponse = inline_serializer(
    name="UsersValidationErrorResponse",
    fields={
        "message": serializers.CharField(required=False),
        "errors": serializers.DictField(required=False),
        "detail": serializers.CharField(required=False),
    },
)

ProfileEnvelopeResponse = inline_serializer(
    name="ProfileEnvelopeResponse",
    fields={
        "message": serializers.CharField(),
        "data": CustomUserSerializer(),
    },
)

PreferencesEnvelopeResponse = inline_serializer(
    name="PreferencesEnvelopeResponse",
    fields={
        "message": serializers.CharField(),
        "data": UserPreferencesSerializer(),
    },
)


class CustomUserViewSet(ViewSet):
    serializer_class = CustomUserSerializer

    def get_serializer_class(self):
        return self.serializer_class

    @action(
        methods=("GET",),
        detail=False,
        url_path="profile",
        url_name="profile",
        permission_classes=(IsAuthenticated,),
    )
    @extend_schema(
        tags=["Auth"],
        summary="Get current authenticated user profile",
        description=(
            "Returns the authenticated user's public profile details. Authentication is required. "
            "Side effects: none besides access logging. Language behavior: `message` is translated "
            "according to resolved request language (`preferred_language`, `?lang=`, or `Accept-Language`). "
            "Timezone behavior: `date_joined` is formatted in the user's configured timezone and locale.\n\n"
            "Request example:\n"
            "GET /api/user/profile/\n"
            "Authorization: Bearer <jwt-access-token>\n\n"
            "Response example (200):\n"
            "{\n"
            "  \"message\": \"Profile retrieved successfully\",\n"
            "  \"data\": {\n"
            "    \"id\": 7,\n"
            "    \"email\": \"alice@example.com\",\n"
            "    \"first_name\": \"Alice\",\n"
            "    \"last_name\": \"Smith\",\n"
            "    \"avatar\": null,\n"
            "    \"date_joined\": \"15:42 10-03-2026\"\n"
            "  }\n"
            "}"
        ),
        responses={
            200: OpenApiResponse(
                response=ProfileEnvelopeResponse,
                description="Profile fetched successfully.",
            ),
            401: OpenApiResponse(
                response=UsersUnauthorizedErrorResponse,
                description="Missing or invalid JWT access token.",
            ),
        },
        examples=[
            OpenApiExample(
                "Profile Success",
                value={
                    "message": "Profile retrieved successfully",
                    "data": {
                        "id": 7,
                        "email": "alice@example.com",
                        "first_name": "Alice",
                        "last_name": "Smith",
                        "avatar": None,
                        "date_joined": "15:42 10-03-2026",
                    },
                },
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "Profile Unauthorized",
                value={"detail": "Authentication credentials were not provided."},
                response_only=True,
                status_codes=["401"],
            ),
        ],
    )
    def profile(
        self,
        request: DRFRequest,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        logger.info(f"Profile request by user_id={request.user.id}")
        serializer: CustomUserSerializer = CustomUserSerializer(
            instance=request.user, context={"request": request}
        )
        logger.debug(f"Profile data retrieved for user_id={request.user.id}")

        return DRFResponse(
            {
                "message": _("Profile retrieved successfully"),
                "data": serializer.data,
            },
            status=HTTP_200_OK,
        )


class UserPreferencesViewSet(ViewSet):
    """
    Singleton resource exposing the authenticated user's language and
    timezone preferences.

    Routes (mapped explicitly in urls.py — no pk required):
        GET  /api/user/preferences/   → retrieve current preferences
        PATCH /api/user/preferences/  → partially update preferences

    Validation is handled by ``UserPreferencesSerializer``:
        - ``preferred_language`` must be in the supported language list.
        - ``timezone`` must be a valid IANA timezone identifier.

    Only authenticated users may access these endpoints.
    """

    permission_classes = (IsAuthenticated,)
    serializer_class = UserPreferencesSerializer

    def get_serializer_class(self):
        return self.serializer_class

    @extend_schema(
        tags=["Auth"],
        summary="Get current user language and timezone preferences",
        description=(
            "Returns the authenticated user's `preferred_language` and `timezone`. "
            "Authentication is required. Side effects: none. Language behavior: response message is "
            "localized by request language resolution middleware. Timezone behavior: this endpoint "
            "returns timezone configuration used later to format datetime fields across API responses.\n\n"
            "Request example:\n"
            "GET /api/user/preferences/\n"
            "Authorization: Bearer <jwt-access-token>\n\n"
            "Response example (200):\n"
            "{\n"
            "  \"message\": \"Preferences retrieved successfully\",\n"
            "  \"data\": {\n"
            "    \"preferred_language\": \"ru\",\n"
            "    \"timezone\": \"Asia/Almaty\"\n"
            "  }\n"
            "}"
        ),
        responses={
            200: OpenApiResponse(
                response=PreferencesEnvelopeResponse,
                description="Preferences retrieved successfully.",
            ),
            401: OpenApiResponse(
                response=UsersUnauthorizedErrorResponse,
                description="Missing or invalid JWT access token.",
            ),
        },
        examples=[
            OpenApiExample(
                "Preferences Get Success",
                value={
                    "message": "Preferences retrieved successfully",
                    "data": {
                        "preferred_language": "ru",
                        "timezone": "Asia/Almaty",
                    },
                },
                response_only=True,
                status_codes=["200"],
            )
        ],
    )
    def retrieve(
        self,
        request: DRFRequest,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        """Return the current user's saved preferences."""

        serializer = UserPreferencesSerializer(instance=request.user)
        return DRFResponse(
            {
                "message": _("Preferences retrieved successfully"),
                "data": serializer.data,
            },
            status=HTTP_200_OK,
        )

    @extend_schema(
        tags=["Auth"],
        summary="Partially update user language/timezone preferences",
        description=(
            "Partially updates authenticated user's `preferred_language` and/or `timezone`. "
            "Authentication is required. Side effects: updates persisted user profile settings "
            "used by language middleware and datetime formatting in subsequent requests. "
            "Language behavior: validation/error messages may be localized. Timezone behavior: "
            "new timezone is used for future datetime serialization.\n\n"
            "Request example:\n"
            "PATCH /api/user/preferences/\n"
            "Authorization: Bearer <jwt-access-token>\n"
            "{\n"
            "  \"preferred_language\": \"kk\",\n"
            "  \"timezone\": \"Asia/Almaty\"\n"
            "}\n\n"
            "Response example (200):\n"
            "{\n"
            "  \"message\": \"User preferences updated successfully\",\n"
            "  \"data\": {\n"
            "    \"preferred_language\": \"kk\",\n"
            "    \"timezone\": \"Asia/Almaty\"\n"
            "  }\n"
            "}"
        ),
        request=UserPreferencesSerializer,
        responses={
            200: OpenApiResponse(
                response=PreferencesEnvelopeResponse,
                description="Preferences updated successfully.",
            ),
            400: OpenApiResponse(
                response=UsersValidationErrorResponse,
                description="Invalid language/timezone payload.",
            ),
            401: OpenApiResponse(
                response=UsersUnauthorizedErrorResponse,
                description="Missing or invalid JWT access token.",
            ),
        },
        examples=[
            OpenApiExample(
                "Preferences Patch Request",
                value={
                    "preferred_language": "kk",
                    "timezone": "Asia/Almaty",
                },
                request_only=True,
            ),
            OpenApiExample(
                "Preferences Patch Success",
                value={
                    "message": "User preferences updated successfully",
                    "data": {
                        "preferred_language": "kk",
                        "timezone": "Asia/Almaty",
                    },
                },
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "Preferences Patch Validation Error",
                value={
                    "message": "Invalid input data",
                    "errors": {"timezone": ["Invalid timezone."]},
                },
                response_only=True,
                status_codes=["400"],
            ),
        ],
    )
    def partial_update(
        self,
        request: DRFRequest,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        """
        Partially update the current user's preferences.

        Accepted fields:
            ``preferred_language`` — one of: en, ru, kk
            ``timezone``           — valid IANA identifier, e.g. Asia/Almaty

        Example::

            PATCH /api/user/preferences/
            {
                "preferred_language": "ru",
                "timezone": "Asia/Almaty"
            }

        Returns 200 on success, 400 when validation fails.
        """

        logger.info(f"User preferences update request by user_id={request.user.id}")

        serializer = UserPreferencesSerializer(
            instance=request.user,
            data=request.data,
            partial=True,
        )

        if serializer.is_valid():
            serializer.save()
            logger.debug(
                f"User preferences updated for user_id={request.user.id}"
            )
            return DRFResponse(
                {
                    "message": _("User preferences updated successfully"),
                    "data": serializer.data,
                },
                status=HTTP_200_OK,
            )

        logger.warning(
            f"User preferences update failed for user_id={request.user.id}: "
            f"{serializer.errors}"
        )
        return DRFResponse(
            {
                "message": _("Invalid input data"),
                "errors": serializer.errors,
            },
            status=HTTP_400_BAD_REQUEST,
        )
