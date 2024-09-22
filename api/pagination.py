from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 5  # Default number of items per page
    page_size_query_param = 'page_size'
    max_page_size = 100

    def paginate_queryset(self, queryset, request, view=None):
        # Check if ?page=all is in the query parameters
        if request.query_params.get('page') == 'all':
            # Store all results in an attribute for later use in the response
            self.all_results = queryset
            return None
        
        # Otherwise, paginate as usual
        return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data):
        # If page=all, return the entire queryset in 'results' and count the total elements
        if hasattr(self, 'all_results'):
            return Response({
                'count': self.all_results.count(),
                'results': list(self.all_results)  # Return all items in 'results'
            })
        
        # Normal paginated response
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })
