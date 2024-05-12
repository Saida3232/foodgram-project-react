import base64

from django.core.files.base import ContentFile
from django.core.exceptions import ObjectDoesNotExist
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from webcolors import hex_to_name, hex_to_rgb

from foodgram.models import (Favorite, Follow, Ingredient, RecipeIngredient,
                             Recipe, ShoppingCart, Tag)
from user.models import User


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:image"):
            format, imgstr = data.split(";base64,")
            ext = format.split("/")[-1]

            data = ContentFile(base64.b64decode(imgstr), name="temp." + ext)

        return super().to_internal_value(data)


class Hex2NameColor(serializers.Field):
    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        try:
            hex_to_rgb(data)
            data = hex_to_name(data)
        except ValueError:
            raise serializers.ValidationError("Для этого цвета нет имени")
        return data


class TagSerializer(serializers.ModelSerializer):
    color = Hex2NameColor()

    class Meta:
        model = Tag
        fields = "__all__"


class BaseRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class FavoriteOrShoppingRecipeSerializer(BaseRecipeSerializer):

    class Meta(BaseRecipeSerializer.Meta):
        read_only_fields = ("__all__",)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class CustomUserSerializer(UserCreateSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "email", "username", "first_name",
                  "last_name", "is_subscribed")

    def get_is_subscribed(self, obj):
        user = self.context.get("request").user
        if user.is_authenticated:
            return Follow.objects.filter(user=user, author=obj.id).exists()
        return False


class CustomCreateUserSerializer(CustomUserSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "username",
                  "first_name", "last_name", "password")
        extra_kwargs = {"password": {"write_only": True}}


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit")

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class ReadRecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = UserSerializer()
    ingredients = RecipeIngredientSerializer(
        source="ingredients_for_recipe", many=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "name",
            "image",
            "tags",
            "text",
            "cooking_time",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
        )

    def get_is_favorited(self, obj):
        request = self.context.get("request")
        user = request.user
        if user.is_authenticated:
            return Favorite.objects.filter(user=user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get("request")
        user = request.user
        if user.is_authenticated:
            return ShoppingCart.objects.filter(user=user, recipe=obj).exists()
        return False


class CreateIngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ("id", "amount")


class CreateRecipeSerializer(serializers.ModelSerializer):
    ingredients = CreateIngredientSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all())
    image = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = Recipe
        fields = (
            "ingredients",
            "tags",
            "name",
            "image",
            "text",
            "cooking_time",
            "created",
        )

    def validate(self, data):
        ingredients = data.get("ingredients")
        id_ingredients = [ingredient['id'] for ingredient in ingredients]

        tags = data.get("tags")
        try:
            for ingredient_id in id_ingredients:
                Ingredient.objects.get(pk=ingredient_id)
        except ObjectDoesNotExist as e:
            raise serializers.ValidationError(f"Ингредиент с id {ingredient_id} не существует")

        if not ingredients:
            raise serializers.ValidationError(
                "Нужно добавить хотя бы один ингредиент")
        elif len(id_ingredients) != len(set(id_ingredients)):
            raise serializers.ValidationError('Нельзя добавлять одинаковые ингредиенты')
        if not tags:#спросить к Георгия почему теги не нужно засовывать в список
            raise serializers.ValidationError(
                "Нужно добавить хотя бы один тег.")
        elif len(tags) != len(set(tags)):
            raise serializers.ValidationError('Нельзя добавлять одинаковые теги.')


        return data

    def create_ingredients(self, ingredients, recipe):
        for element in ingredients:
            id = element["id"]
            ingredient = Ingredient.objects.get(pk=id)
            amount = element["amount"]
            RecipeIngredient.objects.create(
                ingredient=ingredient, recipe=recipe, amount=amount
            )


    def create(self, validated_data):
        ingredients = validated_data.pop("ingredients")
        tags = validated_data.pop("tags")

        user = self.context.get("request").user
        recipe = Recipe.objects.create(**validated_data, author=user)
        self.create_ingredients(ingredients, recipe)
        recipe.tags.set(tags)
        return recipe

    def update(self, instance, validated_data):
        updated_data = validated_data.copy()

        for attr, value in validated_data.items():
            if attr == "ingredients":
                RecipeIngredient.objects.filter(recipe=instance).delete()
                self.create_ingredients(
                    updated_data.pop("ingredients"), instance)
            elif attr == "tags":
                instance.tags.set(value)
            else:
                setattr(instance, attr, value)

        instance.save()
        return instance

    def to_representation(self, instance):
        return ReadRecipeSerializer(instance, context=self.context).data


class FollowSerializer(UserSerializer):
    recipes_count = serializers.ReadOnlyField(source="recipes.count")
    recipes = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + (
            "recipes",
            "recipes_count",
        )
        read_only_fields = ("email", "username", "first_name", "last_name")

    def get_recipes(self, obj):
        recipes = obj.recipes.all()
        recipes_limit = self.context.get(
            "request").query_params.get("recipes_limit")
        if recipes_limit:
            recipes = recipes[: int(recipes_limit)]
        return BaseRecipeSerializer(recipes, many=True).data


class FollowCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ("user", "author")

    def validate(self, data):
        user = data.get("user").id
        author = data.get("author").id
        if Follow.objects.filter(
                author=author, user=user).exists():
            raise serializers.ValidationError(
                "Вы уже подписались на этого пользователя.",
            )
        if user == author:
            raise serializers.ValidationError(
                "Нельзя подписаться на самого себя).",
            )
        return data

    def to_representation(self, instance):
        return FollowSerializer(
            instance.author, context=self.context
        ).data
