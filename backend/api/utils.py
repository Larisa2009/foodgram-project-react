from rest_framework.response import Response
from rest_framework import status


class SubscriptionMixin:

    def get_is_subscribed(self, obj):
        if self.context.get('request') and obj:
            user = self.context.get('request').user
            return (user.is_authenticated
                    and user.following == obj)


def serializer_create_delete(user_id, pk, serializer_class=None, model=None):
    if serializer_class:
        serializer = serializer_class(
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

    favorite = model.objects.filter(
        user=user_id,
        recipe=pk
    )
    deleted, _ = favorite.delete()
    if not deleted:
        return Response(
            {'errors': 'Рецепт отсутствует в избранном'},
            status=status.HTTP_400_BAD_REQUEST
        )
    return Response(status=status.HTTP_204_NO_CONTENT)
