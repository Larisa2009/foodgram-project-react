class SubscriptionMixin:

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (
            request
            and obj
            and request.user.is_authenticated
            and request.user.following == obj
        )
