from rest_framework.pagination import PageNumberPagination

from foodgram import consts


class CustomPagination(PageNumberPagination):
    page_size = consts.PAGE_SIZE
    page_size_query_param = "limit"
    max_page_size = consts.MAX_PAGE_SIZE
