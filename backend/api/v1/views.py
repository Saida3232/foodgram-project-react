from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework.permissions import SAFE_METHODS
from rest_framework.decorators import action
# from django_filters import rest_framework
from rest_framework import filters, mixins, status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from foodgram.models import (
    Ingredient,
    Recipe,
    Tag,
)

from .serializers import (
    IngredientSerialiazer,
    RecipeReadSerializer,
    TagSerializer, RecipeCreateSerializer
)


User = get_user_model()


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related("author").prefetch_related(
        "tags", "ingredients")

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeCreateSerializer


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerialiazer
