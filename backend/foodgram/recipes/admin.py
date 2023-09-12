from django.contrib import admin

from recipes.models import (
    Favorite,
    RecipeIngredient,
    Ingredient,
    Recipe,
    Tag,
    Cart
)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    list_filter = ('name', )
    search_fields = ('^name', )


class IngredientInline(admin.TabularInline):
    model = RecipeIngredient
    list_display = ('id', 'recipe', 'ingredient', 'amount')
    list_editable = ('recipe', 'ingredient', 'amount')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color', 'slug')
    list_editable = ('name', 'color', 'slug')
    search_fields = ('^name', 'slug')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = (IngredientInline,)
    list_display = ('id',
                    'name',
                    'author',
                    'text',
                    'image',
                    'favorite_count',
                    'cooking_time')
    readonly_fields = ('favorite_count',)
    list_filter = ('name', 'author', 'tags')

    def tags(self, recipe):
        tags = []
        for tag in recipe.tags.all():
            tags.append(tag.name)
        return ' '.join(tags)

    @admin.display(description='В избранном')
    def favorite_count(self, obj):
        return obj.favorites.count()


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    list_editable = ('user', 'recipe')


@admin.register(Cart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    list_editable = ('user', 'recipe')
