
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as UVS

from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from api.filters import IngredientFilter, RecipeFilter
from api.paginators import PageNumberLimitPaginator
from api.permissions import IsAuthAndIsAuthorOrReadOnly
from api.serializers import (CartSerializer, FavoriteSerializer,
                             IngredientSerializer, RecipeCreateSerializer,
                             RecipeListSerializer, SubscribeSerializer,
                             SubscriptionsSerializer, TagSerializer)
from recipes.models import (Cart, Favorite, Ingredient, Recipe,
                            RecipeIngredient, Tag)
from users.models import Subscribe


FoodgramUser = get_user_model()


class UserViewSet(UVS):
    queryset = FoodgramUser.objects.all()
    filter_backends = (DjangoFilterBackend,)
    permission_classes = (AllowAny,)
    http_method_names = ['get', 'post', 'delete']
    pagination_class = PageNumberLimitPaginator

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(IsAuthenticated,))
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
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted, _ = Subscribe.objects.filter(
            user=user,
            author=author
        ).delete()

        if not deleted:
            return Response(
                {'errors': 'Вы не подписаны на данного пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthAndIsAuthorOrReadOnly])
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
    http_method_names = ('get', 'post', 'patch', 'delete')
    pagination_class = PageNumberLimitPaginator
    permission_classes = (IsAuthenticatedOrReadOnly, )
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeListSerializer
        return RecipeCreateSerializer

    def serializer_create(self, user_id, pk, serializer):
        serializer = serializer(
            data={
                'user': user_id,
                'recipe': pk
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    def serializer_delete(self, user_id, pk, model):
        deleted, _ = model.objects.filter(
            user=user_id,
            recipe=pk
        ).delete()
        if not deleted:
            return Response(
                {'errors': 'Рецепт отсутствует в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated, ])
    def favorite(self, request, **kwargs):
        if request.method == 'POST':
            return self.serializer_create(
                request.user.id,
                kwargs['pk'],
                FavoriteSerializer
            )
        return self.serializer_delete(
            request.user.id,
            kwargs['pk'],
            Favorite
        )

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthAndIsAuthorOrReadOnly])
    def download_shopping_cart(self, request):
        items = RecipeIngredient.objects.select_related(
            'recipe', 'ingredient'
        ).filter(recipe__shopping_carts__user=request.user).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            total=Sum('amount')
        ).order_by('ingredient__name')
        response = self.make_shoplist(items)
        return response

    def make_shoplist(self, items):
        items_list = []
        for item in items:
            items_list.append(
                f"{item['ingredient__name']} - "
                f"{item['total']} {item['ingredient__measurement_unit']}"
            )
        response = HttpResponse(
            '\n'.join(items_list),
            content_type='text/plan'
        )
        response['Content-Disposition'] = 'attachment; filename="shoplist.txt"'
        return response

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthAndIsAuthorOrReadOnly])
    def shopping_cart(self, request, **kwargs):
        if request.method == 'POST':
            return self.serializer_create(
                request.user.id,
                kwargs['pk'],
                CartSerializer
            )
        return self.serializer_delete(
            request.user.id,
            kwargs['pk'],
            Cart
        )


class IngredientViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        GenericViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class TagViewSet(mixins.ListModelMixin,
                 mixins.RetrieveModelMixin,
                 GenericViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
