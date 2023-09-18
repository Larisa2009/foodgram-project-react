from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Subscribe, FoodgramUser


@admin.register(FoodgramUser)
class UserAdmin(UserAdmin):
    list_display = (
        'username',
        'first_name',
        'last_name',
        'email',
        'following',
        'recipes'
    )
    search_fields = ('username', 'email')
    list_filter = ('username', 'email')


@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    list_display = ('user', 'author', )
    search_fields = ('user', 'author', )
