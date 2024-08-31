from django_filters import rest_framework as filters
from .models import *


class CarFilter(filters.FilterSet):
    price_min = filters.NumberFilter(field_name="price_day", lookup_expr='gte')
    price_max = filters.NumberFilter(field_name="price_day", lookup_expr='lte')
    fuel_type = filters.ModelChoiceFilter(queryset=FuelType.objects.all())
    gearbox = filters.ModelChoiceFilter(queryset=Gearbox.objects.all())
    year = filters.NumberFilter()
    brand = filters.ModelChoiceFilter(queryset=BrandCars.objects.all())

    class Meta:
        model = Car
        fields = ['price_min', 'price_max', 'fuel_type', 'gearbox', 'year', 'brand']