from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .models import (Favorite, Follow, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag, TagInRecipe)

User = get_user_model()

admin.site.empty_value_display = 'Не задано'


class IngredientsInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 3


class TagInline(admin.TabularInline):
    model = TagInRecipe
    extra = 3


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("name", "ingredients", "author",
                    'tags', 'cooking_time', 'text')
    inlines = (IngredientsInline,)
    search_fields = ['name', 'author']
    list_filter = ['tags', 'author']
    list_select_related = ['author']
    list_display_links = ['author', 'text', 'name']

    def ingredients(self, obj):
        return ",".join(
            [ingredients.name for ingredients in obj.ingredients.all()])

    def tags(self, obj):
        return ','.join([tags.name for tags in obj.tags.all()])


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ['name']


admin.site.register(User, UserAdmin)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe")
    search_fields = ("user", "recipe")


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    search_fields = ('user', 'author')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe")
    search_fields = ("user", "recipe")
