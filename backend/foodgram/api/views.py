from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.serializers import SetPasswordSerializer
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated



from .serializers import (
    SubscribeSerializer,
    SubscriptionsSerializer,
    UserGetSerializer,
    UserPostSerializer
)
from users.models import Subscribe, FoodgramUser
from .permissions import IsAuthorOnly


class CustomUserViewSet(UserViewSet):
    queryset = FoodgramUser.objects.all()
    filter_backends = (DjangoFilterBackend,)
    permission_classes = (IsAuthenticated,)
    search_fields = ('username', 'email')
    lookup_fields = ('name', 'id')
    http_method_names = ['get', 'post', 'delete']

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return UserGetSerializer
        return UserPostSerializer

    @action(detail=False, methods=['post'],
            permission_classes=(IsAuthenticated,))
    def set_password(self, request):
        serializer = SetPasswordSerializer(data=request.data,
                                           context={'request': request})
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
                data={'user': user.id, 'author': author.id},
                context={"request": request})
            serializer.is_valid(raise_exception=True)
            Subscribe.objects.create(user=user, author=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        subscribe = Subscribe.objects.filter(user=user, author=author)
        if not subscribe:
            return Response({'errors': 'Подписки на этого автора нет!'},
                            status=status.HTTP_400_BAD_REQUEST)
        subscribe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthorOnly])
    def subscriptions(self, request):
        """Метод получения всех подписок."""
        queryset = FoodgramUser.objects.filter(following__user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionsSerializer(
            page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)


