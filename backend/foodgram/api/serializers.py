from djoser.serializers import UserCreateSerializer
from rest_framework import serializers

from recipes.models import Recipe

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
                    author=obj, user=self.context['request'].user).exists()
                )


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
        fields = ('id', 'name', 'image', 'cooking_time')


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
        validators = (
            serializers.UniqueTogetherValidator(
                queryset=Subscribe.objects.all(),
                fields=('user', 'author'),
                message='Подписка уже оформлена'
            ),
        )

    def validate_author(self, data):
        if self.context['request'].user == data:
            raise serializers.ValidationError(
                'Невозможно подписаться на самого себя')
        return data

    def to_representation(self, instance):
        instance = instance['author']
        return SubscriptionsSerializer(instance, context=self.context).data


