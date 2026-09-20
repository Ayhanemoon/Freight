from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination

from core.api_errors import ErrorCode


class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

    def paginate_queryset(self, queryset, request, view=None):
        try:
            return super().paginate_queryset(queryset, request, view)
        except NotFound:
            raise NotFound(
                detail="Invalid page.",
                code=ErrorCode.INVALID_PAGE,
            )