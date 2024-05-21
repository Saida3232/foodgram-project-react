import base64
from webcolors import hex_to_name, hex_to_rgb

from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.db import transaction
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from foodgram.constants import MAX_VALUE, MIN_VALUE
from foodgram.models import (Follow, Ingredient, Recipe,
                             RecipeIngredient, Tag)
from user.models import User


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


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:image"):
            format, imgstr = data.split(";base64,")
            ext = format.split("/")[-1]

            data = ContentFile(base64.b64decode(imgstr), name="temp." + ext)

        return super().to_internal_value(data)


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
    image = Base64ImageField()

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
        user = self.context["request"].user

        if user.is_authenticated:
            return obj.follow.exists()
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
        request = self.context['request']
        user = request.user
        recipe = obj
        if user.is_authenticated:
            return recipe.favorites.exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context['request']
        user = request.user
        recipe = obj
        if user.is_authenticated:
            return recipe.shopping_recipe.exists()
        return False


class CreateIngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=MIN_VALUE, max_value=MAX_VALUE)

    class Meta:
        model = RecipeIngredient
        fields = ("id", "amount")


class CreateRecipeSerializer(serializers.ModelSerializer):
    ingredients = CreateIngredientSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all())
    image = Base64ImageField(use_url=True)
    cooking_time = serializers.IntegerField(
        min_value=MIN_VALUE, max_value=32000)

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
        if ingredients is None:
            raise serializers.ValidationError(
                'Обязательно добавьте поле ингредиентов.')
        id_ingredients = [ingredient['id'] for ingredient in ingredients]

        tags = data.get("tags")
        try:
            for ingredient_id in id_ingredients:
                Ingredient.objects.get(pk=ingredient_id)
        except ObjectDoesNotExist:
            raise serializers.ValidationError(
                f"Ингредиент с id {ingredient_id} не существует")

        if not ingredients:
            raise serializers.ValidationError(
                "Нужно добавить хотя бы один ингредиент")
        if len(id_ingredients) != len(set(id_ingredients)):
            raise serializers.ValidationError(
                'Нельзя добавлять одинаковые ингредиенты')
        if not tags:
            raise serializers.ValidationError(
                "Нужно добавить хотя бы один тег.")
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                'Нельзя добавлять одинаковые теги.')

        return data

    def create_ingredients(self, ingredients, recipe):
        all_ingrediets = []
        for element in ingredients:
            id = element["id"]
            ingredient = Ingredient.objects.get(pk=id)
            amount = element["amount"]
            recipe_ingredient = RecipeIngredient(
                ingredient=ingredient, recipe=recipe, amount=amount
            )
            all_ingrediets.append(recipe_ingredient)

        with transaction.atomic():
            RecipeIngredient.objects.bulk_create(all_ingrediets)

    def create(self, validated_data):
        ingredients = validated_data.pop("ingredients")
        tags = validated_data.pop("tags")

        user = self.context.get("request").user
        recipe = Recipe.objects.create(**validated_data, author=user)
        self.create_ingredients(ingredients, recipe)
        recipe.tags.set(tags)
        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time',
                                                   instance.cooking_time)
        instance.image = validated_data.get('image', instance.image)
        instance.ingredients_for_recipe.all().delete()
        instance.tags_for_the_recipe.all().delete()

        self.create_ingredients(validated_data.pop('ingredients'), instance)
        instance.tags.set(validated_data.pop('tags'))

        instance.save()
        return instance

    def to_representation(self, instance):
        return ReadRecipeSerializer(instance, context=self.context).data


class FollowSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source="recipes.count")

    class Meta(CustomUserSerializer.Meta):
        fields = CustomUserSerializer.Meta.fields + (
            "recipes",
            "recipes_count",
        )
        read_only_fields = ("email", "username", "first_name",
                            "last_name", 'is_subscribed')

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.recipes.all()
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit:
            recipes = recipes[: int(recipes_limit)]
        return BaseRecipeSerializer(recipes, many=True).data


class FollowCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ("user", "author")

    def validate(self, data):
        user = data["user"]
        author = data["author"]
        if author.follow.exists():
            raise serializers.ValidationError(
                "Вы уже подписались на этого пользователя.",
            )
        if user.id == author.id:
            raise serializers.ValidationError(
                "Нельзя подписаться на самого себя).",
            )
        return data

    def to_representation(self, instance):
        return FollowSerializer(
            instance.author, context=self.context
        ).data
