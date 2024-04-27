from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
# from django_filters import rest_framework
from rest_framework import filters, mixins, status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from foodgram.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                             ShoppingCard, Tag, TagRecipe)

from .serializers import (CustomCreateUserSerializer, CustomUserSerializer,
                          FollowSerializer, IngredientSerialiazer,
                          ReceipeAllSerializer, RecipeCreareSerializer,
                          TagSerializer, FavoriteSerialiser)


User = get_user_model()


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().order_by('created')
    http_method_names = ('get', 'post', 'patch', 'head', 'delete')
    permission_classes = (AllowAny,)

    def get_serializer_class(self):
        if self.action in ['retrive', 'list']:
            return ReceipeAllSerializer
        return RecipeCreareSerializer

    def get_recipe(self):
        return get_object_or_404(
            Recipe, pk=self.kwargs['recipe_pk'],
        )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, recipe=self.get_recipe())


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerialiazer
