from django_filters import rest_framework as filters
from .models import Section, Center

class CenterFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')
    description = filters.CharFilter(field_name='description', lookup_expr='icontains')
    location = filters.CharFilter(field_name='location', lookup_expr='icontains')

    class Meta:
        model = Center
        fields = ['name', 'description', 'location', 'latitude', 'longitude']


from django_filters import rest_framework as filters
from .models import Section

class SectionFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')  # Игнорируем регистр
    description = filters.CharFilter(field_name='description', lookup_expr='icontains')
    category = filters.NumberFilter(field_name='category')
    center = filters.NumberFilter(field_name='center')

    class Meta:
        model = Section
        fields = ['name', 'description', 'category', 'center']

