from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import RecipeViewSet, IngredientViewSet, TagViewSet, FavoriteViewSet

router = DefaultRouter()
router.register("recipes", RecipeViewSet, basename="recipe")
router.register("ingredients", IngredientViewSet, basename="ingredient")
router.register('tags', TagViewSet, basename='tag')
router.register(r'recipes/(?P<recipe_pk>\d+)/favorite', FavoriteViewSet, basename='favorite')

urlpatterns = [
    # path('', include(router.urls)),
    path("", include("djoser.urls")),
    path("auth/", include("djoser.urls.authtoken")),
    path("v1/", include(router.urls)),
]
