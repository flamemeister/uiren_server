from rest_framework.pagination import PageNumberPagination

class CenterPagination(PageNumberPagination):
    page_size = 5  # Количество элементов на странице
    page_size_query_param = 'page_size'  # Параметр для изменения размера страницы через запрос
    max_page_size = 100  # Максимальный размер страницы
