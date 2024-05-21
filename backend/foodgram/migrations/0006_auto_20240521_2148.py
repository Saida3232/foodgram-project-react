# Generated by Django 3.2.3 on 2024-05-21 18:48

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('foodgram', '0005_auto_20240511_1139'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='follow',
            options={'ordering': ('-created',), 'verbose_name': 'Подписка', 'verbose_name_plural': 'Подписки'},
        ),
        migrations.AlterModelOptions(
            name='recipeingredient',
            options={'default_related_name': 'ingredients_for_recipe', 'ordering': ('ingredient__name',), 'verbose_name': 'Ингредиент в рецепте', 'verbose_name_plural': 'Ингредиенты в рецептах'},
        ),
        migrations.AlterModelOptions(
            name='shoppingcart',
            options={'default_related_name': 'shopping_recipe', 'verbose_name': 'Список покупок', 'verbose_name_plural': 'Списки покупок'},
        ),
        migrations.AlterModelOptions(
            name='tag',
            options={'ordering': ('name',), 'verbose_name': 'Тег', 'verbose_name_plural': 'Теги'},
        ),
        migrations.AlterModelOptions(
            name='taginrecipe',
            options={'default_related_name': 'tags_for_the_recipe', 'ordering': ('tag__name',), 'verbose_name': 'Тег рецепта', 'verbose_name_plural': 'Теги рецепта'},
        ),
        migrations.AddField(
            model_name='favorite',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='Дата добавления.'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='follow',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='Дата подписки.'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='shoppingcart',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='Дата добавления.'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='recipe',
            name='cooking_time',
            field=models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1, message='Время должно быть больше 1 минуты.'), django.core.validators.MaxValueValidator(32000, message='Не больше 32_000!')], verbose_name='Время готовки'),
        ),
        migrations.AlterField(
            model_name='recipeingredient',
            name='amount',
            field=models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1, message='Минимальное количество 1!'), django.core.validators.MaxValueValidator(32000, message='Не больше 32_000!')], verbose_name='Количество'),
        ),
        migrations.AlterField(
            model_name='recipeingredient',
            name='ingredient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ingredients_for_recipe', to='foodgram.ingredient', verbose_name='Ингредиент'),
        ),
        migrations.AlterField(
            model_name='shoppingcart',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shopping_recipe', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь'),
        ),
        migrations.AlterField(
            model_name='tag',
            name='name',
            field=models.CharField(max_length=100, unique=True, verbose_name='Название'),
        ),
        migrations.AlterField(
            model_name='tag',
            name='slug',
            field=models.SlugField(max_length=100, unique=True, verbose_name='Слаг'),
        ),
        migrations.AlterField(
            model_name='taginrecipe',
            name='recipe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tags_for_the_recipe', to='foodgram.recipe', verbose_name='Рецепт'),
        ),
        migrations.AlterField(
            model_name='taginrecipe',
            name='tag',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tags_for_the_recipe', to='foodgram.tag', verbose_name='Теги'),
        ),
    ]
