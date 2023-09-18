

class SubscriptionMixin:

    def get_is_subscribed(self, obj):
        context = self.context.get('request')
        return (
            context
            and obj
            and context.user.is_authenticated
            and context.user.following == obj
        )
