from djoser.serializers import UserCreateSerializer
from rest_framework import serializers

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