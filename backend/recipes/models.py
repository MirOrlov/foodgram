# models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import (
    MinValueValidator,
    RegexValidator,
)
from django.conf import settings

from foodgram import consts


class User(AbstractUser):
    """Кастомная модель пользователя с дополнительными полями."""

    email = models.EmailField(
        verbose_name="Электронная почта",
        unique=True,
        max_length=254,
    )
    username = models.CharField(
        verbose_name="Логин",
        max_length=consts.MAX_USER_NAME,
        unique=True,
        validators=[RegexValidator(r"^[\w.@+-]+$")],
    )
    first_name = models.CharField(
        verbose_name="Имя",
        max_length=consts.MAX_USER_NAME,
    )
    last_name = models.CharField(
        verbose_name="Фамилия",
        max_length=consts.MAX_USER_NAME,
    )
    avatar = models.ImageField(
        verbose_name="Аватар",
        upload_to="users/avatars/",
        blank=True,
        null=True,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ("email",)

    def __str__(self):
        return f"{self.username} ({self.email})"


class Tag(models.Model):
    """Модель тегов для рецептов."""

    name = models.CharField(
        verbose_name="Название тега",
        max_length=consts.MAX_TAG_NAME,
        unique=True,
    )
    slug = models.SlugField(
        verbose_name="Слаг тега",
        max_length=consts.MAX_TAG_NAME,
        unique=True,
    )

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"
        ordering = ("name",)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиентов для рецептов."""

    name = models.CharField(
        verbose_name="Название ингредиента",
        max_length=consts.MAX_INGREDIENT_NAME,
    )
    measurement_unit = models.CharField(
        verbose_name="Единица измерения",
        max_length=consts.MAX_MEASUREMENT_NAME,
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        ordering = ("name",)

    def __str__(self):
        return f"{self.name}, {self.measurement_unit}"


class Recipe(models.Model):
    """Основная модель рецептов."""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Автор рецепта",
        on_delete=models.CASCADE,
        related_name="recipes",
    )
    name = models.CharField(
        verbose_name="Название рецепта",
        max_length=consts.MAX_RECIPE_NAME,
    )
    text = models.TextField(
        verbose_name="Описание рецепта",
    )
    image = models.ImageField(
        verbose_name="Изображение блюда",
        upload_to="recipes/images/",
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name="Время приготовления (мин)",
        validators=[MinValueValidator(consts.MIN_COOKING_TIME)],
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

    def __str__(self):
        return f"{self.name} (автор: {self.author.username})"


class RecipeIngredient(models.Model):
    """Промежуточная модель для связи рецептов и ингредиентов."""

    recipe = models.ForeignKey(
        Recipe,
        verbose_name="Рецепт",
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name="Ингредиент",
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name="Количество",
        validators=[MinValueValidator(consts.MIN_AMOUNT)],
    )

    class Meta:
        verbose_name = "Ингредиент в рецепте"
        verbose_name_plural = "Ингредиенты в рецептах"
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"],
                name="unique_recipe_ingredient",
            ),
        ]

    def __str__(self):
        return f"{self.ingredient.name} - {self.amount}\
              {self.ingredient.measurement_unit}"


class Subscription(models.Model):
    """Модель подписок пользователей на авторов."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Подписчик",
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
    subscribed_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Автор",
        on_delete=models.CASCADE,
        related_name="subscribers",
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "subscribed_to"],
                name="unique_subscription",
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F("subscribed_to")),
                name="prevent_self_subscription",
            ),
        ]

    def __str__(self):
        return f"{self.user.username} подписан на \
        {self.subscribed_to.username}"


class Favorite(models.Model):
    """Модель избранных рецептов пользователей."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Пользователь",
        on_delete=models.CASCADE,
        related_name="favorites",
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name="Рецепт",
        on_delete=models.CASCADE,
        related_name="favorites",
    )

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранные рецепты"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"],
                name="unique_favorite",
            ),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.recipe.name}"


class ShoppingCart(models.Model):
    """Модель списка покупок пользователей."""

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
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"],
                name="unique_shopping_cart",
            ),
        ]

    def __str__(self):
        return f"Корзина {self.user.username}: {self.recipe.name}"
    