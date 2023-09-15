from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from recipes.models import Ingredient
from drf_base64.fields import Base64ImageField
from recipes.models import Recipe, Favorite, Cart, RecipeIngredient, Tag

from users.models import Subscribe, FoodgramUser


class UserGetSerializer(UserCreateSerializer):
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
        return (self.context['request'].user.is_authenticated
                and Subscribe.objects.filter(
                    author=obj, user=self.context['request'].user).exists())


class UserPostSerializer(UserCreateSerializer):

    class Meta:
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password'
        )
        model = FoodgramUser


class RecipeSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class SubscriptionsSerializer(serializers.ModelSerializer):
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
        return (
            self.context.get('request').user.is_authenticated
            and Subscribe.objects.filter(
                user=self.context['request'].user,
                author=obj).exists()
        )

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

    def validate_author(self, data):
        if self.context['request'].user == data:
            raise serializers.ValidationError(
                'Невозможно подписаться на самого себя')
        return data

    def to_representation(self, instance):
        return SubscriptionsSerializer(
            instance['author'],
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
        instance = instance['recipe']
        return RecipeSimpleSerializer(instance, context=self.context).data


class CartSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('user', 'recipe')
        model = Cart

    def validate_recipe(self, data):
        if Cart.objects.filter(
            recipe=data,
            user=self.context['request'].user
        ).exists():
            raise serializers.ValidationError('Рецепт уже в корзине')
        return data

    def to_representation(self, instance):
        instance = instance['recipe']
        return RecipeSimpleSerializer(instance).data


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


class TagSetSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = Tag

    def to_representation(self, instance):
        tag = Tag.objects.get(id=instance)
        serializer = TagSerializer(tag)
        return serializer.data


class RecipeListSerializer(serializers.ModelSerializer):
    author = UserGetSerializer(read_only=True)
    image = serializers.ImageField()
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientInRecipeSerializer(
        many=True,
        source='recipes'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        exclude = ('pub_date',)

    def get_is_favorited(self, obj):
        if self.context['request'].user.is_anonymous:
            return False
        return Favorite.objects.filter(
            user=self.context['request'].user,
            recipe=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        if self.context['request'].user.is_anonymous:
            return False
        return Cart.objects.filter(
            user=self.context['request'].user,
            recipe=obj
        ).exists()


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = Ingredient


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        depth = 1

    def to_representation(self, instance):
        i = Ingredient.objects.get(id=instance['id'])
        serializer = IngredientSerializer(i)
        self.validate_amount(instance['amount'])
        data = {'amount': instance['amount']}
        data.update(serializer.data)
        return data

    def validate_amount(self, amount):
        if not amount:
            raise serializers.ValidationError(
                'Необходимо задать количество продукта'
            )
        return amount


class RecipeCreateSerializer(serializers.ModelSerializer):
    author = UserGetSerializer(read_only=True)
    image = Base64ImageField()
    ingredients = serializers.SerializerMethodField()
    cooking_time = serializers.IntegerField()
    tags = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        exclude = ('pub_date', )
        depth = 1

    def get_tags(self, obj):
        data = self._kwargs['data']['tags']
        self.validate_tags(data)
        tags = []
        for i in data:
            tag = TagSetSerializer(i)
            tags.append(tag.data)

        return tags

    def get_ingredients(self, obj):
        data = self._kwargs['data']['ingredients']
        self.validate_ingredients(data)
        ingredients = []

        for i in data:
            ingredient = RecipeIngredientCreateSerializer(i)
            ingredients.append(ingredient.data)

        return ingredients

    def create(self, validated_data):
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            text=validated_data.get('text'),
            image=validated_data.get('image'),
            name=validated_data.get('name'),
            cooking_time=validated_data.get('cooking_time')
        )
        for ingredient in self._kwargs['data']['ingredients']:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=Ingredient.objects.get(id=ingredient['id']),
                amount=ingredient['amount']
            )

        recipe.tags.set(self._kwargs['data']['tags'])
        return recipe

    def update(self, recipe, validated_data):
        ingredients = validated_data.get('ingredients')
        tags = validated_data.get('tags')
        recipe.name = validated_data.get('name')
        recipe.text = validated_data.get('text')
        recipe.image = validated_data.get('image')
        recipe.cooking_time = validated_data.get('cooking_time')
        recipe.save()

        if ingredients:
            recipe.ingredients.clear()
            for ingredient in ingredients:
                RecipeIngredient.objects.create(
                    recipe=recipe,
                    ingredient=Ingredient.objects.get(id=ingredient['id']),
                    amount=ingredient['amount']
                )
        if tags:
            recipe.tags.set(tags)
        return recipe

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(
                'В рецепте не могут отсутствовать ингредиенты'
            )
        for ingredient in ingredients:
            if not Ingredient.objects.filter(id=ingredient['id']).exists():
                raise serializers.ValidationError(
                    'Необходимо выбрать ингредиент из списка'
                )
        return ingredients

    def validate_cooking_time(self, cooking_time):
        if not cooking_time:
            raise serializers.ValidationError(
                'Минимальное время приготовления - 1 минута'
            )
        return cooking_time

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError(
                'В рецепте не могут отсутствовать теги'
            )
        for tag in tags:
            if not Ingredient.objects.filter(id=tag).exists():
                raise serializers.ValidationError(
                    'Необходимо выбрать тег из предложеннных'
                )
        return tags
