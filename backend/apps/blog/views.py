# Python modules
from typing import Any

# Third-party modules
from rest_framework.viewsets import ViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response as DRFResponse
from rest_framework.request import Request as DRFRequest
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from rest_framework.decorators import action

# Project modules
from apps.blog.serializers import PostCreateSerializer


class PostViewSet(ViewSet):
    @action(
        methods=("POST",),
        detail=False,
        url_path="posts",
        url_name="posts_create",
        permission_classes=(IsAuthenticated,),
    )
    def create(
        self,
        request: DRFRequest,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        pass

    @action(
        methods=("GET",),
        detail=False,
        url_path="posts",
        url_name="posts_create",
        permission_classes=(AllowAny,),
    )
    def get(
        self,
        request: DRFRequest,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        pass
