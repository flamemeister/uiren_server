from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
import math

class CenterPagination(PageNumberPagination):
    page_size = 5  # Default page size
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        # Ensure the data passed here is serialized
        count_pages = math.ceil(self.page.paginator.count / self.page_size)
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count_pages': count_pages,
            'results': data  # Data here should already be serialized
        })

    def paginate_queryset(self, queryset, request, view=None):
        if 'page' not in request.query_params:
            # If no page parameter is present, return all centers in serialized form
            return None
        return super().paginate_queryset(queryset, request, view)
