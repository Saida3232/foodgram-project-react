import django_filters
from django_filters import rest_framework
from django_filters.rest_framework import FilterSet


class RecipeFilter(FilterSet):
    tags = rest_framework.CharFilter(
        field_name='tags__slug', lookup_expr='exact')
    cooking_time = django_filters.NumberFilter(
        field_name='cooking_time', lookup_expr='lte', label='Максимальное время приготовления рецепта')
    is_favorited = django_filters.NumberFilter(method='favorite')
    in_shopping_cart = django_filters.NumberFilter(method='shopping_cart')
    author = django_filters.NumberFilter(
        field_name='author__id', lookup_expr='exact', label='author')

    def favorite(self, queryset, name, value):
        if value == 1:
            return queryset.filter(favorites__user_id=self.request.user.id)
        return queryset

    def shopping_cart(self, queryset, name, value):
        if value == 1:
            return queryset.filter(shopping_recipe__user_id=self.request.user.id)
        return queryset
