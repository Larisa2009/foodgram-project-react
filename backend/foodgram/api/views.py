from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.serializers import SetPasswordSerializer
from djoser.views import UserViewSet
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from recipes.models import Ingredient, Tag
from recipes.models import Recipe, Favorite, RecipeIngredient, Cart
from django.http import HttpResponse


from .serializers import (
    CartSerializer, IngredientSerializer,
    RecipeCreateSerializer, RecipeListSerializer,
    SubscribeSerializer, SubscriptionsSerializer,
    TagSerializer, UserGetSerializer,
    UserPostSerializer
)
from .serializers import FavoriteSerializer
from users.models import Subscribe, FoodgramUser
from .permissions import IsAuthorOnly


class CustomUserViewSet(UserViewSet):
    queryset = FoodgramUser.objects.all()
    filter_backends = (DjangoFilterBackend,)
    permission_classes = (AllowAny,)
    search_fields = ('username', 'email')
    lookup_fields = ('name', 'id')
    http_method_names = ['get', 'post', 'delete']

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return UserGetSerializer
        return UserPostSerializer

    # @action(detail=True, methods=['get'],
    #         permission_classes=(IsAuthenticated,))
    # def me(self, request):
    #     serializer = UserGetSerializer(
    #         data=request.data
    #     )
    #     serializer.is_valid(raise_exception=True)
    #     user = FoodgramUser.objects.get(serializer.data)
    #     return Response(user)


    @action(detail=False, methods=['post'],
            permission_classes=(IsAuthenticated,))
    def set_password(self, request):
        serializer = SetPasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        self.request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, **kwargs):
        author = get_object_or_404(FoodgramUser, id=kwargs['id'])
        user = request.user
        if request.method == 'POST':
            serializer = SubscribeSerializer(
                data={
                    'user': user.id,
                    'author': author.id
                },
                context={
                    'request': request
                }
            )
            serializer.is_valid(raise_exception=True)
            Subscribe.objects.create(user=user, author=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        subscribe = Subscribe.objects.filter(user=user, author=author)
        if not subscribe:
            return Response({'errors': 'Вы не подписаны на данного автора'},
                            status=status.HTTP_400_BAD_REQUEST)
        subscribe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthorOnly])
    def subscriptions(self, request):
        queryset = FoodgramUser.objects.filter(following__user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionsSerializer(
            page,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    http_method_names = ['get', 'post', 'patch', 'delete']
    

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeListSerializer
        return RecipeCreateSerializer


    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, **kwargs):
        recipe = get_object_or_404(Recipe, id=kwargs['pk'])
        if request.method == 'POST':
            serializer = FavoriteSerializer(
                data={
                    'user': request.user.id,
                    'recipe': recipe.id
                }  
            )
            serializer.is_valid(raise_exception=True)
            Favorite.objects.create(user=request.user, recipe=recipe)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        favorite = Favorite.objects.filter(
            user=request.user.id,
            recipe=recipe.id
        )
        if not favorite:
            return Response(
                {'errors': 'Рецепт отсутствует в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthorOnly])
    def download_shopping_cart(self, request):
        items = RecipeIngredient.objects.select_related(
            'recipe', 'ingredient'
        )
        items = items.filter(recipe__shopping_carts__user=request.user).all()
        cart = items.values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            name='ingredient__name',
            units='ingredient__measurement_unit',
            total=sum('amount')
        )
        response = HttpResponse(cart)
        return response

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, **kwargs):
        recipe = get_object_or_404(Recipe, id=kwargs['pk'])
        if request.method == 'POST':
            serializer = CartSerializer(
                data={
                    'user': request.user.id,
                    'recipe': recipe.id
                },
                context={
                    'request': request
                }
            )
            serializer.is_valid(raise_exception=True)
            Cart.objects.create(user=request.user, recipe=recipe)
            return Response(serializer.data, status=status.HTTP_200_OK)

        cart = Cart.objects.filter(
            recipe=recipe.id,
            user=request.user.id
        )
        if not cart:
            return Response(
                {'errors': 'Рецепт отсутствует в списке покупок'},
                status=status.HTTP_400_BAD_REQUEST
            )
        cart.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class IngredientViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        GenericViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    search_fields = ('name',)


class TagViewSet(mixins.ListModelMixin,
                 mixins.RetrieveModelMixin,
                 GenericViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
