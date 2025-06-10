from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import (
    MinValueValidator,
    RegexValidator,
)
from django.conf import settings


class User(AbstractUser):
    """Модель пользователя."""

    email = models.EmailField(
        verbose_name="Email пользователя",
        unique=True,
        max_length=254,
    )
    username = models.CharField(
        verbose_name="Имя пользователя",
        max_length=settings.MAX_USER_NAME,
        unique=True,
        validators=[RegexValidator(r"^[\w.@+-]+$")],
    )
    first_name = models.CharField(
        verbose_name="Имя",
        max_length=settings.MAX_USER_NAME,
    )
    last_name = models.CharField(
        verbose_name="Фамилия",
        max_length=settings.MAX_USER_NAME,
    )
    avatar = models.ImageField(
        verbose_name="Аватарка",
        upload_to="users/",
        blank=True,
        null=True,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = [
        "username",
        "first_name",
        "last_name",
    ]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ("email",)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Модель подписок пользователей."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Подписчик",
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
    subscribed_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Автор контента",
        on_delete=models.CASCADE,
        related_name="subscribers",
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        ordering = ("user", "subscribed_to")
        constraints = [
            models.UniqueConstraint(
                fields=["user", "subscribed_to"],
                name="unique_subscription_users",
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F("subscribed_to")),
                name="no_self_subscription",
            ),
        ]

    def __str__(self):
        return f"{self.user} → {self.subscribed_to}"


class Ingredient(models.Model):
    """Модель ингредиентов."""

    name = models.CharField(
        verbose_name="Название ингредиента",
        max_length=settings.MAX_INGREDIENT_NAME,
    )
    measurement_unit = models.CharField(
        verbose_name="Единица измерения",
        max_length=settings.MAX_MEASUREMENT_NAME,
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        ordering = ("name",)

    def __str__(self):
        return f"{self.name} ({self.measurement_unit})"


class Tag(models.Model):
    """Модель тегов."""

    name = models.CharField(
        verbose_name="Название тега",
        max_length=settings.MAX_TAG_NAME,
        unique=True,
    )
    slug = models.SlugField(
        verbose_name="Slug тега",
        max_length=settings.MAX_TAG_NAME,
        unique=True,
    )

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"
        ordering = ("name",)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецептов."""

    name = models.CharField(
        verbose_name="Название рецепта",
        max_length=settings.MAX_RECIPE_NAME,
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Автор рецепта",
        on_delete=models.CASCADE,
    )
    text = models.TextField(
        verbose_name="Описание рецепта",
    )
    image = models.ImageField(
        verbose_name="Фото блюда",
        upload_to="recipes/",
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name="Время готовки (мин)",
        validators=[
            MinValueValidator(settings.MIN_COOKING_TIME),
        ],
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name="Ингредиенты",
        through="RecipeIngredient",
        related_name="recipes",
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name="Теги",
        related_name="recipes",
    )

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ("-id",)
        default_related_name = "recipes"

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Модель связи рецептов и ингредиентов."""

    recipe = models.ForeignKey(
        Recipe,
        verbose_name="Рецепт",
        on_delete=models.CASCADE,
    )
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name="Ингредиент",
        on_delete=models.CASCADE,
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name="Количество",
        validators=[
            MinValueValidator(settings.MIN_AMOUNT),
        ],
    )

    class Meta:
        verbose_name = "Ингредиент в рецепте"
        verbose_name_plural = "Ингредиенты в рецептах"
        ordering = ("recipe",)
        default_related_name = "recipe_ingredients"
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"],
                name="unique_recipe_ingredient",
            ),
        ]

    def __str__(self):
        return f"{self.recipe}: {self.ingredient} x{self.amount}"


class Favorite(models.Model):
    """Модель избранных рецептов."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Пользователь",
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name="Рецепт",
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = "Избранный рецепт"
        verbose_name_plural = "Избранные рецепты"
        ordering = ("user", "recipe")
        default_related_name = "favorites"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"],
                name="unique_favorite",
            ),
        ]

    def __str__(self):
        return f"{self.user} ♥ {self.recipe}"


class ShoppingCart(models.Model):
    """Модель списка покупок."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Пользователь",
        on_delete=models.CASCADE,
        related_name="shopping_carts",
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name="Рецепт",
        on_delete=models.CASCADE,
        related_name="in_shopping_carts",
    )

    class Meta:
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"
        ordering = ("user", "recipe")
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"],
                name="unique_shopping_cart",
            ),
        ]

    def __str__(self):
        return f"{self.user} 🛒 {self.recipe}"