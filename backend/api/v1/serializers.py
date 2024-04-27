import base64
import datetime as dt

import webcolors
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from foodgram.models import Favorite, Ingredient, Recipe, Tag, ShoppingCard
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


class ShoppingSerializer:
    pass


class RecipeCreareSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    tags = TagSerializer(many=True, read_only=True)
    image = Base64ImageField(required=False, allow_null=True)
    ingredients = IngredientSerialiazer(many=True, read_only=True)

    class Meta:
        model = Recipe
        fields = (
            "ingredients",
            "tags",
            "image",
            "name",
            "text",
            "cooking_duration",
            "author",
        )

    def create(self, validated_data):
        return super().create(validated_data)


class ReceipeAllSerializer(RecipeCreareSerializer):
    author = CustomUserSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorite",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_duration",
        )

    def get_is_favorite(self, obj):
        user = self.context.get("request").user
        return Favorite.objects.filter(user=user, recipe=obj.id).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get("request").user
        return ShoppingCard.objects.filter(user=user, recipe=obj.id).exists()
