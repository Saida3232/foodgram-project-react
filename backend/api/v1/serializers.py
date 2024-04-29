import base64
import datetime as dt
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.db import transaction
import webcolors
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer
from djoser.serializers import UserSerializer
from rest_framework import serializers
from rest_framework.serializers import PrimaryKeyRelatedField
from rest_framework.validators import UniqueTogetherValidator

from foodgram.models import (
    Favorite,
    Ingredient,
    Recipe,
    Tag,
    TagRecipe,
    ShoppingCard,
    IngredientInRecipe,
)
from user.models import Follow

User = get_user_model()


class Hex2NameColor(serializers.Field):
    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        try:
            data = webcolors.hex_to_name(data)
        except ValueError:
            raise serializers.ValidationError("Для этого цвета нет имени")
        return data


class TagSerializer(serializers.ModelSerializer):
    color = Hex2NameColor()

    class Meta:
        model = Tag
        fields = ("id", "name", "color", "slug")


class IngredientSerialiazer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = "__all__"


class IngredientInRecipeSerialiazer(PrimaryKeyRelatedField, serializers.ModelSerializer):
    # ingredient = serializers.PrimaryKeyRelatedField(source='ingredient_name')
    ingredient = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(source="ingredient.measurement_unit")

    class Meta:
        model = IngredientInRecipe
        fields = ("id", "ingredient", "measurement_unit")


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:image"):
            format, imgstr = data.split(";base64,")
            ext = format.split("/")[-1]

            data = ContentFile(base64.b64decode(imgstr), name="temp." + ext)

        return super().to_internal_value(data)


class CustomUserSerializer(UserCreateSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "email", "username", "first_name", "last_name", "is_subscribed")

    def get_is_subscribed(self, obj):
        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        else:
            return Follow.objects.filter(user=user, following=obj.id).exists()


class CustomCreateUserSerializer(CustomUserSerializer):
    """Сериализатор для создания пользователя
    без проверки на подписку"""

    class Meta:
        """Мета-параметры сериализатора"""

        model = User
        fields = ("email", "id", "username", "first_name", "last_name", "password")
        extra_kwargs = {"password": {"write_only": True}}


class FavoriteSerialiser(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Favorite
        fields = ("id", "recipes__name", "recipes__image", "recipes__cooking_duration")
        validators = UniqueTogetherValidator(
            queryset=Favorite.objects.all(), fields=["user", "recipe"]
        )


class FollowSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    following = CustomUserSerializer(read_only=True)

    class Meta:
        model = Follow
        fields = "following"
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=["user", "following"],
                message="Нельзя дважды подписаться на одного человека.",
            )
        ]

    def validate_following(self, data):
        request = self.context.get("request")
        following = data
        if request.user == following:
            raise serializers.ValidationError("Низя на себя подиписываться,нарцисс.")
        return data


class IngredientsInCreateRecipe(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    @staticmethod
    def validate_amount(value):
        if value < 1:
            raise serializers.ValidationError("Ингредиентов должно быть больше.")
        return value

    class Meta:
        model = IngredientInRecipe
        fields = ("id", "amount")



class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов."""

    tags = TagSerializer(many=True)
    author = UserSerializer()
    ingredients = IngredientsInCreateRecipe(
        source='ingredient_list', many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        """Мета-параметры сериализатора"""

        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart', 'name',
                  'image', 'text', 'cooking_duration'
                  )

    def get_is_favorited(self, obj):
        """Метод проверки на добавление в избранное."""

        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(
            user=request.user, recipe=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        """Метод проверки на присутствие в корзине."""

        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return ShoppingCard.objects.filter(
            user=request.user, recipe=obj
        ).exists()


class ReceipeCreateUpdateSerializer(serializers.ModelSerializer):
    #author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    image = Base64ImageField(required=False, allow_null=True)
    ingredients = IngredientsInCreateRecipe(many=True)
    tags = serializers.PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all())

    class Meta:
        model = Recipe
        fields = (
            "id",
            "name",
            "tags",
            "image",
            "text",
            "ingredients",
            "cooking_duration",
        )

    def to_representation(self, instance):
        """Метод представления модели"""

        serializer = RecipeSerializer(
            instance,
            context={
                'request': self.context.get('request')
            }
        )
        return serializer.data

    def validate(self, data):
        """Метод для валидации данных
        перед созданием рецепта
        """
        ingredients = self.initial_data.get("ingredients")
        if not ingredients:
            raise serializers.ValidationError(
                {"ingredients": "В рецепте отсутсвуют ингредиенты"}
            )
        ingredients_result = []
        for ingredient_item in ingredients:
            ingredient = get_object_or_404(Ingredient,
                                           id=ingredient_item["id"]
                                           )
            if ingredient in ingredients_result:
                raise serializers.ValidationError(
                    "Ингредиент уже добавлен в рецепт"
                )
            amount = ingredient_item["amount"]
            if not (isinstance(ingredient_item["amount"], int)
                    or ingredient_item["amount"].isdigit()):
                raise ValidationError("Неправильное количество ингидиента")
            ingredients_result.append({"ingredients": ingredient,
                                       "amount": amount
                                       })
        data["ingredients"] = ingredients_result
        return data


    def create_ingredients(self, ingredients, recipe):
        for i in ingredients:
            id = i['id']
            ingredient = Ingredient.objects.get(pk=id)
            amount = i['amount']
            IngredientInRecipe.objects.create(
                ingredient=ingredient, recipe=recipe, amount=amount
            )

    @transaction.atomic
    def create(self, validated_data):
        """Метод создания модели"""

        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        user = self.context.get('request').user
        recipe = Recipe.objects.create(**validated_data, author=user)
        self.create_ingredients(ingredients, recipe)
        self.create_tags(tags, recipe)
        return recipe

    def update(self, instance, validated_data):
        """Метод обновления модели"""

        IngredientInRecipe.objects.filter(recipe=instance).delete()
        TagRecipe.objects.filter(recipe=instance).delete()

        self.create_ingredients(validated_data.pop('ingredients'), instance)
        self.create_tags(validated_data.pop('tags'), instance)

        return super().update(instance, validated_data)


class ReceipeListSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(read_only=True, slug_field="username")
    tags = serializers.SlugRelatedField(
        queryset=Tag.objects.all(), slug_field="slug", many=True
    )
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "name",
            "image",
        )
        read_only_fields = ("__all__",)
