from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from foodgram.models import (
    Favorite,
    Follow,
    Ingredient,
    RecipeIngredient,
    Recipe,
    ShoppingCart,
    Tag,
)
from user.models import User

from .filters import RecipeFilter, IngredientFilter
from .permissions import IsAuthorOrOnlyRead
from .serializers import (
    CreateRecipeSerializer,
    CustomUserSerializer,
    FavoriteOrShoppingRecipeSerializer,
    IngredientSerializer,
    ReadRecipeSerializer,
    TagSerializer,
    FollowSerializer,
    FollowCreateSerializer,
)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    search_fields = ("^name",)
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.select_related("author").prefetch_related(
        "tags", "ingredients"
    )
    permission_classes = [IsAuthorOrOnlyRead, IsAuthenticated]
    filter_backends = (DjangoFilterBackend,)
    http_method_names = ("get", "post", "patch", "head", "delete")
    filterset_class = RecipeFilter
    ordering_fields = ["name", "created", "author"]

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return ReadRecipeSerializer
        elif self.action in ("create", "partial_update"):
            return CreateRecipeSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    @action(
        detail=True, permission_classes=(IsAuthenticated,),
        methods=("post", "delete")
    )
    def favorite(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == "POST":
            favorite, created = Favorite.objects.get_or_create(
                user=user, recipe=recipe)
            if not created:
                return Response(
                    "Рецепт уже добавлен в избранное.",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = FavoriteOrShoppingRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == "DELETE":
            try:
                favorite = Favorite.objects.get(user=user, recipe=recipe)
                favorite.delete()
                return Response(
                    "Рецепт добавлен в избранное.",
                    status=status.HTTP_204_NO_CONTENT
                )
            except Favorite.DoesNotExist:
                return Response(
                    "Рецепт не был добавлен в избранное, "
                    "поэтому вы не можете его удалить.",
                    status=status.HTTP_400_BAD_REQUEST,
                )

    @action(
        detail=True, permission_classes=(IsAuthenticated,),
        methods=("post", "delete")
    )
    def shopping_cart(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == "POST":
            cart, created = ShoppingCart.objects.get_or_create(
                user=user, recipe=recipe)
            if not created:
                return Response(
                    "Рецепт уже добавлен в корзину.",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = FavoriteOrShoppingRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == "DELETE":
            try:
                cart = ShoppingCart.objects.get(user=user, recipe=recipe)
                cart.delete()
                return Response(
                    "Рецепт удален из корзины.",
                    status=status.HTTP_204_NO_CONTENT,
                )
            except ShoppingCart.DoesNotExist:
                return Response(
                    "Рецепта не было в корзине, вы не можете его удалить.",
                    status=status.HTTP_400_BAD_REQUEST,
                )

    @action(detail=False,
            permission_classes=(IsAuthenticated,),
            methods=("get",))
    def download_shopping_cart(self, request):
        ingredients = (
            RecipeIngredient.objects.select_related("recipe", "ingredient")
            .filter(recipe__shopping_recipe__user=request.user)
            .values_list("ingredient__name", "ingredient__measurement_unit")
            .annotate(amount=Sum("amount"))
        )
        response_object = HttpResponse(content_type="text/plain")
        response_object["Content-Disposition"] = (
            "attachment; filename=ingredients.txt")

        for ingredient in ingredients:
            response_object.write(
                f"Ингредиент: {ingredient[0]},"
                f"Единица измерения: {ingredient[1]},"
                f" Количество: {ingredient[2]}\n"
            )
        response_object.write(ingredients)
        return response_object


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_permissions(self):
        if self.action == "me":
            return (IsAuthenticated(),)
        elif self.action == 'retrive':
            return (AllowAny(),)
        return super().get_permissions()

    @action(detail=False, methods=["get"],
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        subscriptions = User.objects.filter(follow__user=request.user)
        
        serializer = FollowSerializer(
            subscriptions, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(
        detail=True, methods=["post"],
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        serializer = FollowCreateSerializer(
            data={"user": request.user.id, "author": id},
            context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id=None):
        subscriptions = Follow.objects.filter(user=request.user, author=id)
        if subscriptions.exists():
            subscriptions.delete()
            return Response(
                "Вы отписались от пользователя.",
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            "Вы не подписаны на этого пользователя.",
            status=status.HTTP_400_BAD_REQUEST
        )
