from users.models import Subscribe


class SubscriptionMixin:

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and Subscribe.objects.filter(
                user=request.user,
                author=obj
            ).exists()
        )
