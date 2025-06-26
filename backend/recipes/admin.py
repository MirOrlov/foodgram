from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import mark_safe
from django.db.models import Count

from recipes.models import (
    User, Tag, Ingredient,
    Recipe, RecipeIngredient,
    Subscription, Favorite, ShoppingCart,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name',
                    'recipes_count', 'subscribers_count')
    search_fields = ('username', 'email')
    list_filter = ('is_staff', 'is_superuser')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Личные данные', {
            'fields': ('first_name', 'last_name', 'email', 'avatar')
        }),
        ('Права', {
            'fields': ('is_active', 'is_staff', 'is_superuser')
        }),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _recipes_count=Count('recipes', distinct=True),
            _subscribers_count=Count('subscribers', distinct=True),
        )
        return queryset

    def recipes_count(self, obj):
        return obj._recipes_count
    recipes_count.admin_order_field = '_recipes_count'
    recipes_count.short_description = 'Рецепты'

    def subscribers_count(self, obj):
        return obj._subscribers_count
    subscribers_count.admin_order_field = '_subscribers_count'
    subscribers_count.short_description = 'Подписчики'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'cooking_time', 'favorites_count')
    search_fields = ('name', 'author__username')
    list_filter = ('tags',)
    inlines = (RecipeIngredientInline,)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _favorites_count=Count('favorites', distinct=True),
        )
        return queryset

    @admin.display(description='Изображение')
    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="100" />')
        return "-"

    @admin.display(description='В избранном')
    def favorites_count(self, obj):
        return obj._favorites_count
    favorites_count.admin_order_field = '_favorites_count'

    readonly_fields = ('image_preview',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscribed_to')
    search_fields = ('user__username', 'subscribed_to__username')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
