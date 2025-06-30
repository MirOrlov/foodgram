from django_filters import rest_framework as df_filters

from recipes.models import Recipe, Ingredient, Tag


class IngredientSearchFilter(df_filters.FilterSet):
    """Фильтр для поиска ингредиентов по начальным буквам названия"""

    name = df_filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = ('name',)


class CustomRecipeFilter(df_filters.FilterSet):
    """Расширенный фильтр для рецептов с поддержкой избранного"""

    is_in_shopping_cart = df_filters.BooleanFilter(
        method='filter_shopping_cart'
    )
    is_favorited = df_filters.BooleanFilter(
        method='filter_favorites'
    )
    tags = df_filters.ModelMultipleChoiceFilter(
        field_name="tags__slug",
        to_field_name="slug",
        queryset=Tag.objects.all(),
        conjoined=False,
    )

    class Meta:
        model = Recipe
        fields = (
            "tags",
            'author',
            'is_in_shopping_cart',
            'is_favorited'
        )

    def _apply_user_filter(self, queryset, field_name, enabled):
        """Общий метод для фильтрации по связанным с пользователем полям"""
        if not enabled:
            return queryset

        user = self.request.user
        if user.is_authenticated:
            return queryset.filter(**{field_name: user})
        return queryset.none()

    def filter_shopping_cart(self, queryset, name, value):
        """Фильтрация рецептов в списке покупок пользователя"""
        return self._apply_user_filter(
            queryset,
            "shopping_carts__user",
            value
        )

    def filter_favorites(self, queryset, name, value):
        """Фильтрация избранных рецептов пользователя"""
        return self._apply_user_filter(
            queryset,
            "favorites__user",
            value
        )
