from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework.permissions import SAFE_METHODS
from rest_framework.decorators import action

# from django_filters import rest_framework
from rest_framework import filters, mixins, status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from foodgram.models import Ingredient, Recipe, Tag, Favorite, ShoppingCard

from .serializers import (
    IngredientSerialiazer,
    RecipeReadSerializer,
    TagSerializer,
    RecipeCreateSerializer,
    FavoriteSerialiser,
)


User = get_user_model()


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related("author").prefetch_related(
        "tag", "ingredients"
    )

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeCreateSerializer


class FavoriteViewSet(viewsets.ModelViewSet):
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerialiser
    http_method_names = ("post", "delete", 'get')

    def get_recipe(self):
        return get_object_or_404(
            Recipe,
            id=self.kwargs["recipe_pk"],
        )

    def create(self, request, *args, **kwargs):
        """Добавление рецепта
        в список избранного
        """
        recipes_id = self.kwargs["recipe_pk"]
        recipes = get_object_or_404(Recipe, id=recipes_id)
        Favorite.objects.create(user=request.user, recipe=recipes)
        serializer = FavoriteSerialiser()
        return Response(
            serializer.to_representation(instance=recipes),
            status=status.HTTP_201_CREATED,
        )

    def delete(self, request, *args, **kwargs):
        recipe = get_object_or_404(
            Recipe,
            id=self.kwargs["recipe_pk"],
        )
        favorite_recipe = get_object_or_404(Favorite, user=request.user,
                                            recipe=recipe)
        favorite_recipe.delete()
        return Response(
            "Рецепт {recipe} удален из избранного.",
            status=status.HTTP_204_NO_CONTENT
        )


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerialiazer
