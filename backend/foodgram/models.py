from django.contrib.auth import get_user_model
from django.db import models
from django.core.validators import RegexValidator, MinValueValidator
User = get_user_model()


class Tag(models.Model):
    name = models.CharField('name', max_length=16, unique=True)
    color = models.CharField('color', max_length=7, unique=True,validators=[
        RegexValidator(
            regex='^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$',
            message='this code is not HEX-color')],
        default = 'ff9bff',
        help_text = 'write some color or it will be pink'
    )
    slug = models.SlugField('slug', max_length=50, unique=True)

    class Meta:
        verbose_name = 'tag'
        verbose_name_plural = 'tags'
        constraints = (models.UniqueConstraint(fields=('name', 'color', 'slug'),
                                               name='unique_tag'),)


class Ingredient(models.Model):
    name = models.CharField('name',max_length=150)
    edinica = models.CharField('edinica',max_length=150)


class Recipe(models.Model):
    author = models.ForeignKey(User, verbose_name=
        'recipes', on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    image = models.ImageField(
        upload_to='recipes/images/',
        null=True,
        default=None
    )
    text = models.TextField("text")
    ingredients = models.ManyToManyField(Ingredient, through='IngredientInRecipe',
                                         related_name='recipes',)
    tag = models.ManyToManyField(Tag, verbose_name="recipes")
    cooking_duration = models.DurationField("time for cooking")

class IngredientInRecipe(models.Model):
    recipe = models.ForeignKey(Recipe, verbose_name="recipe", on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, verbose_name='ingredient', on_delete=models.CASCADE)