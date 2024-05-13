import django_filters
from django_filters import rest_framework
from django_filters.rest_framework import FilterSet

from foodgram.models import Tag

class RecipeFilter(FilterSet):
    tags = django_filters.ModelMultipleChoiceFilter(field_name='tags__slug',
                                                    to_field_name='slug',
                                                    lookup_expr='exact',
                                                    queryset=Tag.objects.all()
                                                    )
    cooking_time = django_filters.NumberFilter(
        field_name='cooking_time', lookup_expr='lte', label='Максимальное время приготовления рецепта')
    is_favorited = django_filters.NumberFilter(method='favorite')
    is_in_shopping_cart = django_filters.NumberFilter(method='shopping_cart')
    is_in_shopping_cart
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

class IngredientFilter(FilterSet):
    name = rest_framework.CharFilter(field_name='name', lookup_expr='startswith')