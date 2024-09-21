from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
import math

class CenterPagination(PageNumberPagination):
    page_size = 5  # Количество элементов на странице
    page_size_query_param = 'page_size'
    max_page_size = 100  # Максимальное количество элементов на одной странице

    def get_paginated_response(self, data):
        # Рассчитываем количество страниц
        count_pages = math.ceil(self.page.paginator.count / self.page_size)

        return Response({
            'count': self.page.paginator.count,  # Общее количество элементов
            'next': self.get_next_link(),  # Ссылка на следующую страницу (если есть)
            'previous': self.get_previous_link(),  # Ссылка на предыдущую страницу (если есть)
            'count_pages': count_pages,  # Количество страниц
            'results': data  # Данные на текущей странице
        })
