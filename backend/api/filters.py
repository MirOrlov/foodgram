from django_filters import rest_framework as filters

from recipes.models import Recipe, Ingredient, Tag


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = (
            'name',
        )


class RecipeFilter(filters.FilterSet):
    is_in_shopping_cart = filters.BooleanFilter(method='filter_in_cart')
    is_favorited = filters.BooleanFilter(method='filter_favorited')
    tags = filters.ModelMultipleChoiceFilter(
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

    def filter_favorited(self, recipes, name, value):
        user = self.request.user
        if value:
            if user.is_authenticated:
                return recipes.filter(favorites__user=user)
            return recipes.none()
        return recipes

    def filter_in_cart(self, recipes, name, value):
        user = self.request.user
        if value:
            if user.is_authenticated:
                return recipes.filter(in_shopping_carts__user=user)
            return recipes.none()
        return recipes
