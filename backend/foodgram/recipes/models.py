from colorfield.fields import ColorField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from users.models import FoodgramUser


class Ingredient(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name='ингредиент',
    )
    measurement_unit = models.CharField(
        max_length=200,
        verbose_name='Единица измерения'
    )


    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Tag(models.Model):
    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name='Название'
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name='Уникальный слаг'
    )
    color = ColorField(
        max_length=7,
        default='#FF0000',
        unique=True,
        verbose_name='Цвет в HEX'
    )


    def __str__(self):
        return self.name

class Tag(models.Model):
    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name='Название'
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name='Уникальный слаг'
    )
    color = ColorField(
        max_length=7,
        default='#FF0000',
        unique=True,
        verbose_name='Цвет в HEX'
    )


    def __str__(self):
        return self.name
class Recipe(models.Model):
    name = models.CharField(max_length=200)
    author = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги'
    )

    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe',
        through_fields=('recipe', 'ingredient'),
        verbose_name='ингредиенты',
    )
    image = models.ImageField(upload_to='recipes/media')
    text = models.TextField(verbose_name='Описание')
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления',
        default=1,
        validators=[
            MinValueValidator(1, 'Разрешены значения от 1 до 200'),
            MaxValueValidator(200, 'Разрешены значения от 1 до 200')
        ]
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )


    def __str__(self):
        return f'{self.name}, {self.author}'




class Favorite(models.Model):
    user = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Добавил в избранное'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Избранный рецепт'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]

class IngredientInRecipe(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredients',
        verbose_name='Ингредиент'
    )
    amount = models.PositiveIntegerField(
        verbose_name='Количество',
        default=1,
        validators=[
            MinValueValidator(1, 'Разрешены значения от 1 до 2000'),
            MaxValueValidator(2000, 'Разрешены значения от 1 до 2000')
        ]
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Рецепт'

    )

class ShoppingCart(models.Model):
    user = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        related_name='shopping_carts',
        verbose_name='Добавил в корзину'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_carts',
        verbose_name='Рецепт в корзине'
    )

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзина'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart'
            )
        ]
