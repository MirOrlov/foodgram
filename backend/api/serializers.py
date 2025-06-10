from django.core.validators import MinValueValidator
from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField
from djoser.serializers import (
    UserSerializer as DjoserUserSerializer,
    UserCreateSerializer as DjoserRegistrationSerializer,
    SetPasswordSerializer as DjoserSetPasswordSerializer,
)
from django.conf import settings

from recipes.models import (
    Recipe,
    RecipeIngredient,
    Ingredient,
    User,
    Tag,
)


class RecipeShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = [
            "id",
            "name",
            "image",
            "cooking_time",
        ]
        read_only_fields = fields


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = [
            "id",
            "name",
            "measurement_unit",
        ]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = [
            "id",
            "name",
            "slug",
        ]


class UserSerializer(DjoserUserSerializer):
    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        fields = [
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        ]
        read_only_fields = [
            'id',
            'is_subscribed',
        ]

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        return (
            request
            and request.user.is_authenticated
            and request.user.subscriptions.filter(subscribed_to=obj).exists()
        )


class UserSubscriptionSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source="recipes.count")

    class Meta:
        model = User
        fields = [
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
            "avatar",
        ]
        read_only_fields = fields

    def get_recipes(self, obj):
        request = self.context.get("request")
        recipes = obj.recipes.all()
        try:
            limit = int(request.GET.get("recipes_limit", 10 ** 10))
            recipes = recipes[:limit] if limit > 0 else recipes.none()
        except (ValueError, TypeError):
            pass
        serializer = RecipeShortSerializer(
            recipes,
            many=True,
            read_only=True,
            context=self.context,
        )
        return serializer.data


class AvatarSerializer(serializers.Serializer):
    avatar = Base64ImageField(required=True)


class RecipeIngredientSerializer(serializers.ModelSerializer):
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
        validators=[
            MinValueValidator(settings.MIN_AMOUNT),
        ],
    )

    class Meta:
        model = RecipeIngredient
        fields = [
            "id",
            "name",
            "measurement_unit",
            "amount",
        ]


class RecipeSerializer(serializers.ModelSerializer):
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
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    cooking_time = serializers.IntegerField(
        validators=[
            MinValueValidator(settings.MIN_COOKING_TIME),
        ],
    )

    class Meta:
        model = Recipe
        fields = [
            "id",
            "author",
            "tags",
            "ingredients",
            "name",
            "image",
            "text",
            "cooking_time",
            "is_favorited",
            "is_in_shopping_cart",
        ]

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(
                "Поле Ингридиент не может быть пустым."
            )
        ingredient_ids = [ingredient["ingredient"]["id"] for ingredient in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                "Ингредиенты не должны повторяться."
            )
        return ingredients

    def validate(self, data):
        """Общая валидация данных"""
        request = self.context['request']
        tags = data.get("tags", [])

        if not tags:
            raise serializers.ValidationError(
                {"tags": "Поле Тег не должно дублироваться"}
            )
        tag_ids = [tag.id for tag in tags]
        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError(
                {"tags": "Теги не должны дублироваться"}
            )
        if request.method == 'POST':
            if 'image' not in self.initial_data or not self.initial_data.get('image'):
                raise serializers.ValidationError(
                    {"image": ["Изображение не должно быть пустым"]}
                )
        elif request.method in ['PATCH', 'PUT']:
            if 'image' in self.initial_data and not self.initial_data.get('image'):
                raise serializers.ValidationError(
                    {"image": ["Изображение не должно быть пустым"]}
                )
            if 'ingredients' not in self.initial_data or not self.initial_data.get('ingredients'):
                raise serializers.ValidationError(
                    {"ingredients": ["Поле Ингридиент обязательно"]}
                )

        return data

    def get_is_favorited(self, obj):
        request = self.context.get("request")
        return (
            request
            and request.user.is_authenticated
            and obj.favorites.filter(user=request.user).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.in_shopping_carts.filter(
                user=request.user,
            ).exists()
        return False

    def _create_or_update_ingredients(self, recipe, ingredients_data):
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=ingredient_data["ingredient"]["id"].id,
                amount=ingredient_data["amount"],
            )
            for ingredient_data in ingredients_data
        )

    def create(self, validated_data):
        ingredients_data = validated_data.pop("recipe_ingredients", [])
        tags_data = validated_data.pop("tags", [])
        recipe = super().create(validated_data)
        recipe.tags.set(tags_data)
        self._create_or_update_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop("recipe_ingredients", [])
        tags_data = validated_data.pop("tags", [])
        instance.recipe_ingredients.all().delete()
        instance.tags.set(tags_data)
        self._create_or_update_ingredients(
            super().update(instance, validated_data),
            ingredients_data,
        )
        return instance

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["tags"] = TagSerializer(
            instance.tags.all(),
            many=True,
        ).data
        return rep


UserRegistrationSerializer = DjoserRegistrationSerializer
SetPasswordSerializer = DjoserSetPasswordSerializer