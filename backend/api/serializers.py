from django.core.validators import MinValueValidator
from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField
from djoser.serializers import (
    UserSerializer as DjoserUserSerializer
)
from foodgram import consts
from api.short_serializers import RecipeShortSerializer

from recipes.models import (
    Recipe,
    RecipeIngredient,
    Ingredient,
    Tag,
)


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient."""

    class Meta:
        model = Ingredient
        fields = ["id", "name", "measurement_unit"]


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag."""

    class Meta:
        model = Tag
        fields = ["id", "name", "slug"]


class UserSerializer(DjoserUserSerializer):
    """Расширенный сериализатор пользователя с поддержкой подписок."""

    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        fields = [
            'email', 'id', 'username',
            'first_name', 'last_name',
            'is_subscribed', 'avatar',
        ]
        read_only_fields = ['id', 'is_subscribed']

    def get_is_subscribed(self, obj):
        """Проверяет, подписку текущего пользователя на пользователя."""
        request = self.context.get("request")
        return (request and request.user.is_authenticated
                and request.user.subscriptions
                .filter(subscribed_to=obj).exists()
                )


class UserSubscriptionSerializer(UserSerializer):
    """Сериализатор для отображения подписок пользователя."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source="recipes.count")

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ["recipes", "recipes_count"]
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
        fields = ["id", "name", "measurement_unit", "amount"]


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
        """Общая валидация данных рецепта."""
        request = self.context['request']
        tags = data.get("tags", [])
        if not tags:
            raise serializers.ValidationError(
                {"tags": "Теги должны быть без дубликатов"}
            )
        tag_ids = [tag.id for tag in tags]

        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError(
                {"tags": "Теги не должны дублироваться"}
            )

        if request.method == 'POST':
            if (
                    'image' not in self.initial_data or not self
                    .initial_data.get('image')
            ):
                raise serializers.ValidationError(
                    {"image":
                        ["Изображение должно быть заполненно"]
                     }
                )
        elif request.method in ['PATCH', 'PUT']:
            if (
                    'image' in self.initial_data and not self
                    .initial_data.get('image')
            ):
                raise serializers.ValidationError(
                    {"image":
                        ["Изображение не должно быть пустым"]
                     }
                )
            if (
                    'ingredients' not in self.initial_data or not self
                    .initial_data.get('ingredients')
            ):
                raise serializers.ValidationError(
                    {"ingredients": ["Ингридиенты должны быть заполненны"]}
                )
        return data

    def validate_ingredients(self, ingredients):
        """Проверяет валидность списка ингредиентов."""

        if not ingredients:
            raise serializers.ValidationError(
                "Ингридиенты должны быть заполненными"
            )
        ingredient_ids = [ing["ingredient"]["id"] for ing in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                "Ингридиенты должны быть без дубликатов")
        return ingredients

    def get_is_favorited(self, obj):
        """Проверяет, добавлен ли рецепт в избранное."""
        request = self.context.get("request")
        return (request and request.user.is_authenticated
                and obj.favorites.filter(user=request.user).exists()
                )

    def get_is_in_shopping_cart(self, obj):
        """Проверяет, добавлен ли рецепт в список покупок."""
        request = self.context.get("request")
        return (request and request.user.is_authenticated
                and obj.in_shopping_carts.filter(user=request.user).exists()
                )

    def create(self, validated_data):
        """Создает новый рецепт с ингредиентами и тегами."""
        ingredients_data = validated_data.pop("recipe_ingredients", [])

        tags_data = validated_data.pop("tags", [])
        recipe = super().create(validated_data)
        recipe.tags.set(tags_data)

        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=ingredient_data["ingredient"]["id"].id,
                amount=ingredient_data["amount"],
            )
            for ingredient_data in ingredients_data
        )
        return recipe

    def update(self, instance, validated_data):
        """Обновляет существующий рецепт с ингредиентами и тегами."""
        ingredients_data = validated_data.pop("recipe_ingredients", [])
        tags_data = validated_data.pop("tags", [])

        # Сначала обновляем основные поля рецепта
        instance = super().update(instance, validated_data)

        # Обновляем теги
        instance.tags.set(tags_data)

        # Удаляем старые ингредиенты и добавляем новые
        instance.recipe_ingredients.all().delete()

        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=instance,
                ingredient=ingredient_data["ingredient"]["id"],
                amount=ingredient_data["amount"],
            )
            for ingredient_data in ingredients_data
        ])

        return instance
