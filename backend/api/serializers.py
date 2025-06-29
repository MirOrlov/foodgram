from django.core.validators import MinValueValidator
from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField
from djoser.serializers import (
    UserSerializer as DjoserUserSerializer
)
from foodgram import consts

from recipes.models import (
    Recipe,
    RecipeIngredient,
    Ingredient,
    User,
    Tag,
    Favorite,
ShoppingCart,
Subscription,
)


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag."""

    class Meta:
        model = Tag
        fields = '__all__'


class UserSerializer(DjoserUserSerializer):
    """Расширенный сериализатор пользователя с поддержкой подписок."""

    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        fields = DjoserUserSerializer.Meta.fields + ('is_subscribed', 'avatar')
        read_only_fields = ('id', 'is_subscribed')

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на данного пользователя."""
        request = self.context.get("request")
        return (
                request and request.user.is_authenticated
                and request.user.subscriptions.filter(subscribed_to=obj).exists()
        )


class UserSubscriptionSerializer(UserSerializer):
    """Сериализатор для отображения подписок пользователя."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source="recipes.count")

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ("recipes", "recipes_count")
        read_only_fields = fields

    def get_recipes(self, obj):
        """Возвращает ограниченное количество рецептов пользователя."""
        request = self.context.get("request")
        recipes = obj.recipes.all()

        try:
            limit = int(request.GET.get("recipes_limit"))
            recipes = recipes[:limit]
        except (ValueError, TypeError):
            pass

        return RecipeShortSerializer(
            recipes, many=True, context=self.context
        ).data

    def validate(self, data):
        """Валидация при создании подписки"""
        user = data.get('user')
        subscribed_to = data.get('subscribed_to')

        if user and subscribed_to and user == subscribed_to:
            raise serializers.ValidationError(
                {'subscribed_to': 'Нельзя подписаться на самого себя'}
            )

        if user and subscribed_to and Subscription.objects.filter(
                user=user,
                subscribed_to=subscribed_to
        ).exists():
            raise serializers.ValidationError(
                {'subscribed_to': 'Вы уже подписаны на этого пользователя'}
            )

        return data

class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления рецепта в избранное."""
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, data):
        """Проверяет, не добавлен ли рецепт уже в избранное."""
        user = data['user']
        recipe = data['recipe']

        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                f"Рецепт '{recipe.name}' уже в избранном"
            )
        return data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления рецепта в корзину покупок."""
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        extra_kwargs = {
            'recipe': {'write_only': True},
            'user': {'write_only': True}
        }

    def validate(self, data):
        """Проверяет, не добавлен ли рецепт уже в корзину."""
        user = data['user']
        recipe = data['recipe']

        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                f"Рецепт '{recipe.name}' уже в корзине покупок"
            )
        return data

    def to_representation(self, instance):
        """Возвращает краткое представление рецепта после добавления."""
        return RecipeShortSerializer(
            instance.recipe,
            context=self.context
        ).data


class AvatarSerializer(serializers.Serializer):
    """Сериализатор для загрузки аватара пользователя."""

    avatar = Base64ImageField(required=True)


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для связи рецепта и ингредиента."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source="ingredient.id",
    )
    name = serializers.CharField(
        source="ingredient.name",
        read_only=True,
    )
    measurement_unit = serializers.CharField(
        source="ingredient.measurement_unit",
        read_only=True,
    )
    amount = serializers.IntegerField(
        validators=[MinValueValidator(consts.MIN_AMOUNT)]
    )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор для краткого представления рецепта."""

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")
        read_only_fields = fields


class RecipeSerializer(serializers.ModelSerializer):
    """Основной сериализатор для модели Recipe."""
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True,
        source="recipe_ingredients",
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        write_only=True,
    )
    image = Base64ImageField(required=True, allow_null=False)
    cooking_time = serializers.IntegerField(
        validators=[MinValueValidator(consts.MIN_COOKING_TIME)]
    )
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            "id", "author", "tags", "ingredients",
            "name", "image", "text", "cooking_time",
            "is_favorited", "is_in_shopping_cart"
        ]

    def to_representation(self, instance):
        """Добавляет полные данные тегов в ответ."""

        rep = super().to_representation(instance)
        rep["tags"] = TagSerializer(
            instance.tags.all(),
            many=True,
        ).data

        return rep

    def validate(self, data):
        tags = data.get('tags', [])
        ingredients = data.get('recipe_ingredients', [])
        image = data.get(
            'image',
        )
        if not tags:
            raise serializers.ValidationError({'tags': 'Поле tags не может быть пустым'})
        tag_ids = [tag.id for tag in tags]
        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError(
                {'tags': 'Дублирование не применимо.'}
            )
        if not ingredients:
            raise serializers.ValidationError(
                {'recipe_ingredients': 'Поле ingredients не может быть пустым'}
            )
        ingredients_ids = [
            ingredient['ingredient']['id'].id for ingredient in ingredients
        ]
        if len(ingredients_ids) != len(set(ingredients_ids)):
            raise serializers.ValidationError(
                {'tags': 'Дублирование не применимо.'}
            )
        if not image:
            raise serializers.ValidationError(
                {'image': 'Изображение нельзя оставить пустым'}
            )

        return data

    @staticmethod
    def _create_recipe_ingredients(recipe, ingredients_data):
        """Создает связи рецепта с ингредиентами."""
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient_data["ingredient"]["id"],
                amount=ingredient_data["amount"],
            )
            for ingredient_data in ingredients_data
        ])

    def create(self, validated_data):
        """Создает новый рецепт с ингредиентами и тегами."""
        ingredients_data = validated_data.pop("recipe_ingredients", [])
        tags_data = validated_data.pop("tags", [])

        recipe = super().create(validated_data)
        recipe.tags.set(tags_data)
        self._create_recipe_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        """Обновляет существующий рецепт с ингредиентами и тегами."""
        ingredients_data = validated_data.pop("recipe_ingredients", [])
        tags_data = validated_data.pop("tags", [])

        instance = super().update(instance, validated_data)
        instance.tags.set(tags_data)
        instance.recipe_ingredients.all().delete()
        self._create_recipe_ingredients(instance, ingredients_data)
        return instance

    def get_is_favorited(self, obj):
        """Проверяет, добавлен ли рецепт в избранное."""
        request = self.context.get("request")
        return (
                request and request.user.is_authenticated
                and obj.favorites.filter(user=request.user).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        """Проверяет, добавлен ли рецепт в список покупок."""
        request = self.context.get("request")
        return (
                request and request.user.is_authenticated
                and obj.shopping_carts.filter(user=request.user).exists()
        )
