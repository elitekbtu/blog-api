# Third-party modules
from rest_framework.pagination import CursorPagination


class DefaultPagination(CursorPagination):
    """
    DefaultPagination for pagination responces
    """

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 200
    ordering = "-created_at", "-id"
