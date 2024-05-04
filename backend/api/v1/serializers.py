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
    name = serializers.ReadOnlyField(source='recipe.name')
    image = Base64ImageField(required=False, allow_null=True)
    cooking_duration = serializers.IntegerField(source='recipe.cooking_duration')

    class Meta:
        model = Favorite
        fields = ("id", "name", "image", "cooking_duration")
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


class AmountIngredientSerializer(PrimaryKeyRelatedField, serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    name = serializers.CharField(source="ingredient.name", read_only=True)
    measurement_unit = serializers.CharField(
        source="ingredient.measurement_unit", read_only=True
    )
    class Meta:
        model = IngredientInRecipe
        fields = ["id", "name", "measurement_unit", "amount"]

    class Meta:
        model = IngredientInRecipe
        fields = ("ingredient_id", "ingredient_name", "ingredient_measurement_unit")


class CreateAmountIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), )
    amount = serializers.IntegerField(
        min_value=1,
        max_value=300,
        error_messages={
            "min_value": "Значение должно быть не меньше {min_value}.",
            "max_value": "Количество ингредиента не больше {max_value}"}
    )

    class Meta:
        fields = ("id", "amount")
        model = IngredientInRecipe


class RecipeReadSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tag = TagSerializer(many=True, read_only=True)
    ingredients = AmountIngredientSerializer(read_only=True,
        many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tag",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_duration",
        )

    def get_is_favorited(self, obj):
        return self.get_is_in_user_field(obj, "favorite")

    def get_is_in_shopping_cart(self, obj):
        return self.get_is_in_user_field(obj, "shoppingcard_user")

    def get_is_in_user_field(self, obj, field):
        request = self.context.get("request")
        return (request.user.is_authenticated and getattr(
            request.user, field).filter(recipe=obj).exists())


class RecipeCreateSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=False, allow_null=True)
    author = UserSerializer(read_only=True)
    tag = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    ingredients = CreateAmountIngredientSerializer(many=True, write_only=True)
    cooking_duration = serializers.IntegerField(
        min_value=1,
        max_value=300,
        error_messages={
            "min_value":
            f"Время приготовления не может быть меньше {1} минуты.",
            "max_value":
            f"Время приготовления не может быть больше {300} минут."
        }
    )

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tag",
            "author",
            "ingredients",
            "name",
            "image",
            "text",
            "cooking_duration",
        )

    def validate(self, data):
        ingredients = self.initial_data.get("ingredients")
        unique_ingredients = []
        if not ingredients:
            raise serializers.ValidationError(
                {"ingredients": "Поле ингредиентов не может быть пустым!"}
            )
        for ingredient in ingredients:
            if ingredient['id'] in unique_ingredients:
                raise serializers.ValidationError('value must be unique!')
            unique_ingredients.append(ingredient['id'])

        tag = data.get("tag")
        if not tag:
            raise serializers.ValidationError(
                {"tag": "Поле тегов не может быть пустым!"}
            )
        return data


    @staticmethod
    def create_ingredients(recipe, ingredients):
        create_ingredients = [
            IngredientInRecipe(
                recipe=recipe, ingredient=ingredient["id"],
                amount=ingredient["amount"]
            )
            for ingredient in ingredients
        ]
        IngredientInRecipe.objects.bulk_create(create_ingredients)

    @transaction.atomic
    def create(self, validated_data):
        current_user = self.context.get("request").user
        tag = validated_data.pop("tag")
        ingredients = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(**validated_data, author=current_user)
        recipe.tag.set(tag)
        self.create_ingredients(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.tag.clear()
        instance.tag.set(validated_data.pop("tag"))
        instance.ingredients.clear()
        ingredients = validated_data.pop("ingredients")
        self.create_ingredients(instance, ingredients)
        return super().update(instance, validated_data)

    def to_representation(self, recipe):
        return RecipeReadSerializer(recipe, context=self.context).data
