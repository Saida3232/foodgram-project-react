from rest_framework.pagination import PageNumberPagination

class LimitNumberPagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = 'limit'
    