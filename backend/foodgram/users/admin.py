from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Subscribe, FoodgramUser


admin.site.register(Subscribe)


@admin.register(FoodgramUser)
class UserAdmin(UserAdmin):
    list_display = (
        'username',
        'first_name',
        'last_name',
        'email',
    )
    search_fields = ('username', 'email')



