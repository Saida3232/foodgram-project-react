from rest_framework import viewsets
from foodgram.models import Tag, Recipe, Ingredient
from .serializers import TagSerializer


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer