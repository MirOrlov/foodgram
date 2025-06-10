from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.db.models import Count, Prefetch
from django.utils.html import mark_safe
from django.contrib import admin

from recipes.models import (
    User, Subscription,
    Ingredient, Recipe, RecipeIngredient,
    Favorite, ShoppingCart, Tag,
)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "measurement_unit", "recipes_cnt")
    search_fields = ("name", "measurement_unit")
    list_filter = ("measurement_unit",)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            recipes_cnt=Count("recipes")
        )

    @admin.display(description="В рецептах", ordering="recipes_cnt")
    def recipes_cnt(self, ingredient):
        return ingredient.recipes_cnt

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    list_filter = ("name",)
    search_fields = ("name", "slug")



@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ("id", "recipe", "ingredient", "amount")
    list_select_related = ("recipe", "ingredient")

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        "id", "name", "cooking_time", "author",
        "fav_cnt", "products_html", "image_preview",
    )
    search_fields = ("name", "author__username", "author__email")
    readonly_fields = ("image_preview",)
    list_select_related = ("author",)
    list_filter = ("tags", )

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .annotate(fav_cnt=Count("favorites"))
            .prefetch_related(
                Prefetch(
                    "recipe_ingredients",
                    RecipeIngredient.objects.select_related("ingredient"),
                )
            )
        )

    @admin.display(description="В избранном", ordering="fav_cnt")
    def fav_cnt(self, recipe):
        return recipe.fav_cnt

    @admin.display(description="Продукты")
    @mark_safe
    def products_html(self, recipe):
        return "<br>".join((
            f"{ri.ingredient.name} — "
            f"{ri.amount} {ri.ingredient.measurement_unit}"
            for ri in recipe.recipe_ingredients.all()
        ))

    @admin.display(description="Картинка")
    def image_preview(self, recipe):
        if recipe.image:
            return mark_safe(f'<img src="{recipe.image.url}" style="max-height: 100px; max-width: 100px;" />')
        return "Нет изображения"


@admin.register(Favorite, ShoppingCart)
class FavoriteAndShoppingCartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "recipe")
    list_filter = ("user", "recipe")
    search_fields = ("user__username", "recipe__name")
    list_select_related = ("user", "recipe")


@admin.register(User)
class CustomUserAdmin(DjangoUserAdmin):
    list_display = (
        "id", "username", "full_name", "email",
        "avatar_preview", "recipes_cnt", "subs_cnt", "followers_cnt",
    )
    search_fields = ("username", "email", "first_name", "last_name")

    readonly_fields = ("avatar_preview",)

    fieldsets = (
    (None, {"fields": ("username", "password")}),
    (
        "Персональная информация",
        {"fields": ("first_name", "last_name", "email", "avatar", "avatar_preview")},
    ),
    (
        "Права доступа",
        {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
    ),
    ("Важные даты", {"fields": ("last_login", "date_joined")}),
    )

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .annotate(
                recipes_cnt=Count("recipes", distinct=True),
                subs_cnt=Count("subscriptions", distinct=True),
                followers_cnt=Count("subscribers", distinct=True),
            )
        )

    @admin.display(description="ФИО", ordering="first_name")
    def full_name(self, user):
        return f"{user.first_name} {user.last_name}".strip()

    @admin.display(description="Аватар")
    def avatar_preview(self, user):
        if user.avatar:  # Проверяем наличие аватара
            return mark_safe(
                f'<img src="{user.avatar.url}" style="max-height: 100px; max-width: 100px; border-radius: 50%;" />')
        return "Нет аватара"
    @admin.display(description="Рецептов", ordering="recipes_cnt")
    def recipes_cnt(self, user):
        return user.recipes_cnt

    @admin.display(description="Подписок", ordering="subs_cnt")
    def subs_cnt(self, user):
        return user.subs_cnt

    @admin.display(description="Подписчики", ordering="followers_cnt")
    def followers_cnt(self, user):
        return user.followers_cnt


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "subscribed_to")
    list_select_related = ("user", "subscribed_to")