class DynamicPaginationMixin:
    """
    DynamicPaginationMixin for Pagination
    """

    cursor_page_size = None
    cursor_ordering = None

    def paginate_queryset(self, queryset):
        if not self.pagination_class:
            return None
        paginator = self.pagination_class()

        if self.cursor_page_size:
            paginator.page_size = self.cursor_page_size

        if self.cursor_ordering:
            paginator.ordering = self.cursor_ordering
        self.paginator = paginator

        return paginator.paginate_queryset(queryset, self.request, view=self)
