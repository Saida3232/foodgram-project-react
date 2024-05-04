from django.contrib import admin

# Register your models here.
from .models import Ingredient, Recipe, TagRecipe,  IngredientInRecipe, Favorite, ShoppingCard


class IngredientGenreInline(admin.TabularInline):
    model = IngredientInRecipe
    extra = 3



@admin.register(Recipe)
class RecipewAdmin(admin.ModelAdmin):
    list_display = ('name', 'ingredients', 'author')
    inlines = (IngredientGenreInline,)
    def ingredients(self, obj):
        return ','.join([ingredients.name for ingredients in obj.ingredients.all()])

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')