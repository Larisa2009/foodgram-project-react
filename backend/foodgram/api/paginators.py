from rest_framework.pagination import PageNumberPagination


class FoodPaginator(PageNumberPagination):
    page_size_query_param = 'limit'
    page_query_param = 'page'
