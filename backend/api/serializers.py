from django.contrib.auth import get_user_model
from django.db.transaction import atomic
from djoser.serializers import UserCreateSerializer
from drf_base64.fields import Base64ImageField

from recipes.models import (Cart, Favorite, Ingredient, Recipe,
                            RecipeIngredient, Tag)

from rest_framework import serializers

from users.models import Subscribe
from api.utils import SubscriptionMixin


FoodgramUser = get_user_model()


class UserGetSerializer(SubscriptionMixin, UserCreateSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )
        model = FoodgramUser

    def get_is_subscribed(self, obj):
        return super().get_is_subscribed(obj)


class RecipeSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class SubscriptionsSerializer(SubscriptionMixin, serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = FoodgramUser
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_is_subscribed(self, obj):
        return super().get_is_subscribed(obj)

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        serializer = RecipeSimpleSerializer(
            recipes, many=True, read_only=True)
        return serializer.data


class SubscribeSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = Subscribe
        validators = (
            serializers.UniqueTogetherValidator(
                queryset=Subscribe.objects.all(),
                fields=('user', 'author'),
                message='Вы уже подписаны на этого автора!'
            ),
        )

    def validate_author(self, author):
        if self.context['request'].user == author:
            raise serializers.ValidationError(
                'Невозможно подписаться на самого себя')
        return author

    def to_representation(self, instance):
        return SubscriptionsSerializer(
            instance.author,
            context=self.context
        ).data


class FavoriteSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('user', 'recipe')
        model = Favorite
        validators = (
            serializers.UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже в избранном'
            ),
        )

    def to_representation(self, instance):
        return RecipeSimpleSerializer(instance.recipe, context=self.context).data


class CartSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('user', 'recipe')
        model = Cart
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Cart.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже в корзине'
            )
        ]

    def to_representation(self, instance):
        return RecipeSimpleSerializer(instance['recipe']).data


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = Tag


class RecipeListSerializer(serializers.ModelSerializer):
    author = UserGetSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientInRecipeSerializer(
        read_only=True,
        many=True,
        source='recipes'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        exclude = ('pub_date', )

    def get_is_favorited(self, obj):
        return (
            self.context.get('request')
            and self.context['request'].user.is_authenticated
            and Favorite.objects.filter(
                user=self.context['request'].user,
                recipe=obj
            ).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        return (
            self.context.get('request')
            and self.context['request'].user.is_authenticated
            and Cart.objects.filter(
                user=self.context['request'].user,
                recipe=obj
            ).exists()
        )


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = Ingredient


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
    )
    amount = serializers.IntegerField(
        max_value=2000,
        min_value=1
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    ingredients = RecipeIngredientCreateSerializer(many=True)
    cooking_time = serializers.IntegerField(
        min_value=1,
        max_value=2000
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )

    class Meta:
        model = Recipe
        exclude = ('pub_date', 'author')

    def create_ingredients(self, recipe, ingredients):
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=Ingredient.objects.get(id=ingredient['id'].id),
                amount=ingredient['amount']
            ) for ingredient in ingredients
        ])

    @atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data
        )
        self.create_ingredients(recipe, ingredients)
        recipe.tags.set(tags)
        return recipe

    @atomic
    def update(self, recipe, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe.ingredients.clear()
        self.create_ingredients(ingredients)
        recipe.tags.set(tags)
        return super().update(recipe, validated_data)

    def validate(self, attrs):
        if not attrs['ingredients']:
            raise serializers.ValidationError(
                'В рецепте не могут отсутствовать ингредиенты'
            )
        if not attrs['tags']:
            raise serializers.ValidationError(
                'В рецепте не могут отсутствовать теги'
            )
        ingredients = []
        for ingredient in attrs['ingredients']:
            if ingredient not in ingredients:
                ingredients.append(ingredient)
        tags = []
        for tag in attrs['tags']:
            if tag not in tags:
                tags.append(tag)
        attrs['ingredients'] = ingredients
        attrs['tags'] = tags
        return attrs

    def to_representation(self, instance):
        return RecipeListSerializer(instance).data
