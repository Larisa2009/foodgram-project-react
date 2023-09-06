from colorfield.fields import ColorField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

# from users.models import User


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


class Recipe(models.Model):
    name = models.CharField(max_length=200)
    author = models.ForeignKey(
        'User',
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


