from django.contrib.auth import get_user_model
from django.core.validators import (MaxValueValidator, MinValueValidator,
                                    RegexValidator)
from django.db import models

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(max_length=150, unique=True,
                            verbose_name="Название")
    slug = models.SlugField(max_length=150, unique=True, verbose_name="Слаг")
    color = models.CharField(
        "Цвет",
        max_length=16,
        unique=True,
        validators=[
            RegexValidator(
                regex="^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$",
                message="Такого цвета нет. Проверьте код.",
            )
        ],
    )

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"
        constraints = (
            models.UniqueConstraint(
                fields=("name", "color", "slug"),
                name="unique_tags",
            ),
        )

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=200, verbose_name="Название"
    )

    measurement_unit = models.CharField(
        max_length=200, verbose_name="Единица измерения"
    )

    class Meta:
        ordering = ("name",)
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"

    def __str__(self):
        return f"{self.name}, {self.measurement_unit}"


class Recipe(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название")
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Автор рецепта",
    )
    image = models.ImageField(
        verbose_name="Фото", upload_to="recipes/", blank=True
    )
    cooking_time = models.PositiveSmallIntegerField(
        "Время готовки",
        validators=[
            MinValueValidator(1, message='Время должно быть больше 1 минуты.'),
        ],
    )
    text = models.TextField(verbose_name="Описание")
    ingredients = models.ManyToManyField(
        Ingredient,
        through="RecipeIngredient",
        verbose_name="Ингредиенты",
    )
    tags = models.ManyToManyField(
        Tag, verbose_name="Теги")
    created = models.DateTimeField(
        auto_now_add=True, db_index=True, verbose_name="Дата публикации."
    )

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        default_related_name = 'recipes'
        ordering = ("-created",)

    def __str__(self):
        return f'{self.name}, {self.author}'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name="Ингредиент",
        validators=[
            MinValueValidator(1, message="Минимальное количество 1!"),
            MaxValueValidator(5760, message='Не больше 4 суток!')
        ],
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name="Количество",
        validators=[
            MinValueValidator(1, message="Минимальное количество 1!"),
        ],
    )

    class Meta:
        verbose_name = "Ингредиент в рецепте"
        verbose_name_plural = "Ингредиенты в рецептах"
        default_related_name = 'ingredients_for_recipe'
        constraints = [
            models.UniqueConstraint(
                fields=("recipe", "ingredient"),
                name="unique_ingredients_in_the_recipe"
            )
        ]

    def __str__(self):
        return f"{self.ingredient} {self.recipe}"


class TagInRecipe(models.Model):
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name="Теги",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
    )

    class Meta:
        verbose_name = "Тег рецепта"
        verbose_name_plural = "Теги рецепта"
        constraints = [
            models.UniqueConstraint(
                fields=["tag", "recipe"], name="unique_tag_and_recipe")
        ]

    def __str__(self):
        return f"{self.tag} {self.recipe}"


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="shopping_user",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="shopping_recipe",
        verbose_name="Рецепт",
    )

    class Meta:
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_shoppingcart"
            )
        ]

    def __str__(self):
        return f"{self.user} {self.recipe}"


class Follow(models.Model):
    author = models.ForeignKey(
        User,
        related_name="follow",
        on_delete=models.CASCADE,
        verbose_name="Автор рецепта",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower",
        verbose_name="Подписчик",
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "author"], name="unique_follow")
        ]

    def __str__(self):
        return f"Пользователь {self.user} подписался на {self.author}"


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
    )

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"
        default_related_name = 'favorites'
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_favorite")
        ]

    def __str__(self):
        return f"Пользователь {self.user} добавил {self.recipe} в избранное."