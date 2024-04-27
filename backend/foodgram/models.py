from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

User = get_user_model()


class Tag(models.Model):
    name = models.CharField('name', max_length=16, unique=True)
    color = models.CharField('color', max_length=7, unique=True, validators=[
        RegexValidator(
            regex='^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$',
            message='this code is not HEX-color')],
        default='ff9bff',
        help_text='write some color or it will be pink'
    )
    slug = models.SlugField('slug', max_length=50, unique=True)

    class Meta:
        verbose_name = 'tag'
        verbose_name_plural = 'tags'
        constraints = (models.UniqueConstraint(fields=('name', 'color', 'slug'),
                                               name='unique_tag'),)


class Ingredient(models.Model):
    name = models.CharField('name', max_length=150)
    measurement_unit = models.CharField('edinica', max_length=150)

    def __str__(self) -> str:
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User, verbose_name='recipes', on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    image = models.ImageField(
        upload_to='recipes/images/',
        null=True,
        default=None
    )
    text = models.TextField("text")
    ingredients = models.ManyToManyField(Ingredient, through='IngredientInRecipe',
                                         related_name='recipes',)
    tag = models.ManyToManyField(
        Tag, verbose_name="recipes", through='TagRecipe')
    cooking_duration = models.IntegerField("time for cooking", validators=[
        MinValueValidator(1)])
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class IngredientInRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe, verbose_name="recipe", on_delete=models.CASCADE)
    ingredient = models.ForeignKey(
        Ingredient, verbose_name='ingredient', on_delete=models.CASCADE)
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[
            MinValueValidator(1, message='Минимальное количество 1!'),
        ]
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_ingredients_in_the_recipe'
            )
        ]

    def __str__(self):
        return f'{self.ingredient} {self.recipe}'


class TagRecipe(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, verbose_name="tag")
    recipe = models.ForeignKey(
        Recipe, verbose_name="recipe", on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Тег рецепта'
        verbose_name_plural = 'Теги рецепта'
        constraints = [
            models.UniqueConstraint(fields=['tag', 'recipe'],
                                    name='unique_tagrecipe')
        ]

    def __str__(self):
        return f'{self.tag} {self.recipe}'


class Favorite(models.Model):
    user = models.ForeignKey(User, verbose_name='user',
                             on_delete=models.CASCADE, related_name='favorite')
    recipe = models.ForeignKey(
        Recipe, verbose_name='recipe', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_favorite'
            )
        ]

    def __str__(self):
        return f'{self.user} {self.recipe}'


class ShoppingCard(models.Model):
    user = models.ForeignKey(User, verbose_name='user',
                             on_delete=models.CASCADE, related_name='shoppingcard_user')
    recipe = models.ForeignKey(Recipe, verbose_name='recipe',
                               on_delete=models.CASCADE, related_name='shoppingcard_recipe')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_shoppingcart'
            )
        ]

    def __str__(self):
        return f'{self.user} {self.recipe}'
