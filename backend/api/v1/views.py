from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
    SAFE_METHODS
)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from foodgram.models import (
    Favorite,
    Ingredient,
    RecipeIngredient,
    Recipe,
    ShoppingCart,
    Tag,
)
from user.models import User
from .filters import RecipeFilter, IngredientSearch
from .paginations import LimitNumberPagination
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


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_permissions(self):
        if self.action == "me":
            return (IsAuthenticated(),)
        if self.action == 'retrive':
            return (AllowAny(),)
        return super().get_permissions()

    @action(detail=False, methods=["get"],
            permission_classes=[IsAuthenticated],
            pagination_class=LimitNumberPagination)
    def subscriptions(self, request):
        subscriptions = User.objects.filter(follow__user=request.user)
        if subscriptions is None:
            return Response('Вы еще ни на кого не подписались.',
                            status=status.HTTP_400_BAD_REQUEST)
        pages = self.paginate_queryset(subscriptions)
        serializer = FollowSerializer(pages, many=True,
                                      context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True, methods=["post", 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        author = get_object_or_404(User, id=id)
        if request.method == 'POST':
            serializer = FollowCreateSerializer(
                data={"user": request.user.id, "author": id},
                context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)

        if request.method == "DELETE":
            if request.user.follower.filter(author=author).exists():
                request.user.follower.filter(author=author).delete()
                return Response(
                    "Вы отписались от пользователя.",
                    status=status.HTTP_204_NO_CONTENT
                )
            return Response(
                "Вы не подписаны на этого пользователя.",
                status=status.HTTP_400_BAD_REQUEST
            )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (IngredientSearch,)
    search_fields = ("^name",)
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.select_related("author").prefetch_related(
        "tags", "ingredients"
    )
    permission_classes = [IsAuthorOrOnlyRead, ]
    filter_backends = (DjangoFilterBackend,)
    http_method_names = ("get", "post", "patch", "head", "delete")
    filterset_class = RecipeFilter
    ordering_fields = ["name", "created", "author"]
    pagination_class = LimitNumberPagination

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return ReadRecipeSerializer
        return CreateRecipeSerializer

    @action(
        detail=True, permission_classes=(IsAuthenticated,),
        methods=("post", "delete")
    )
    def favorite(self, request, pk=None):
        user = request.user

        if request.method == "POST":
            try:
                recipe = Recipe.objects.get(pk=pk)
            except Recipe.DoesNotExist:
                return Response(
                    "Такого рецепта не существует.",
                    status=status.HTTP_400_BAD_REQUEST,
                )
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
            recipe = get_object_or_404(Recipe, pk=pk)
            try:
                favorite = Favorite.objects.get(user=user, recipe=recipe)
                favorite.delete()
                return Response(
                    "Удалили рецепт из избранного",
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

        if request.method == "POST":
            try:
                recipe = Recipe.objects.get(pk=pk)
            except Recipe.DoesNotExist:
                return Response(
                    "Такого рецепта не существует.",
                    status=status.HTTP_400_BAD_REQUEST,
                )
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
            recipe = get_object_or_404(Recipe, pk=pk)
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

        for ingredient, measurement_unit, amount in ingredients:
            response_object.write(
                f"Ингредиент: {ingredient},"
                f"Единица измерения: {measurement_unit},"
                f"Количество: {amount}\n"
            )
        return response_object
