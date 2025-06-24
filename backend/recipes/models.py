from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator


class User(AbstractUser):
    """Пользовательская модель"""
    first_name = models.CharField(
        max_length=settings.MAX_USER_NAME,
        verbose_name="имя",
    )
    last_name = models.CharField(
        max_length=settings.MAX_USER_NAME,
        verbose_name="фамилия",
    )  
    username = models.CharField(
        max_length=settings.MAX_USER_NAME,
        validators=[RegexValidator(r"^[\w.@+-]+$")],
        unique=True,
        verbose_name="никнейм",
    )
    email = models.EmailField(
        unique=True,
        max_length=254,
        verbose_name="е-mail",
    )
    avatar = models.ImageField(
        upload_to="users/",
        null=True,
        blank=True,
        verbose_name="фото профиля",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username",
                       "first_name",
                       "last_name",]

    class Meta:
        verbose_name_plural = "пользователи"
        verbose_name = "пользователь"
        ordering = ("email",)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Подписки пользователя"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions",
        verbose_name="подписчик",
    )
    subscribed_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscribers",
        verbose_name="автор",
    )

    class Meta:
        verbose_name = "подписка"
        verbose_name_plural = "подписки"
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
    """Ингридиенты"""

    measurement_unit = models.CharField(
        max_length=settings.MAX_MEASUREMENT_NAME,
        verbose_name="единица измерения",
    )
    name = models.CharField(
        max_length=settings.MAX_INGREDIENT_NAME,
        verbose_name="название ингредиента",
    )

    class Meta:
        verbose_name = "ингредиент"
        verbose_name_plural = "ингредиенты"
        ordering = ("name",)

    def __str__(self):
        return f"{self.name} ({self.measurement_unit})"


class Tag(models.Model):
    """Теги"""

    name = models.CharField(
        max_length=settings.MAX_TAG_NAME,
        unique=True,
        verbose_name="название тега",
    )
    slug = models.SlugField(
        max_length=settings.MAX_TAG_NAME,
        unique=True,
        verbose_name="slug тега",
    )

    class Meta:
        ordering = ("name",)
        verbose_name = "тег"
        verbose_name_plural = "теги"

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Рецепты"""

    name = models.CharField(
        max_length=settings.MAX_RECIPE_NAME,
        verbose_name="имя рецепта",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="автор",
    )
    text = models.TextField(
        verbose_name="рецепт",
    )
    image = models.ImageField(
        upload_to="recipes/",
        verbose_name="фото",
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(settings.MIN_COOKING_TIME),
        ],
        verbose_name="время приготовления",
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through="RecipeIngredient",
        related_name="recipes",
        verbose_name="ингредиенты",
    )
    tags = models.ManyToManyField(
        Tag,
        related_name="recipes",
        verbose_name="теги",
    )

    class Meta:
        ordering = ("-id",)
        default_related_name = "recipes"
        verbose_name = "рецепт"
        verbose_name_plural = "рецепты"

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Рецепты и ингредиенты"""
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name="ингредиент",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="рецепт",
    )

    amount = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(settings.MIN_AMOUNT),
        ],
        verbose_name="количество",
    )

    class Meta:
        ordering = ("recipe",)
        default_related_name = "recipe_ingredients"
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"],
                name="unique_recipe_ingredient",
            ),
        ]
        verbose_name = "ингредиент в рецепте"
        verbose_name_plural = "ингредиенты в рецептах"

    def __str__(self):
        return f"{self.recipe}: {self.ingredient} x{self.amount}"


class Favorite(models.Model):
    """Избранные рецепты"""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="рецепт",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="пользователь",
    )

    class Meta:
        ordering = ("user", "recipe")
        default_related_name = "favorites"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"],
                name="unique_favorite",
            ),
        ]
        verbose_name = "избранный рецепт"
        verbose_name_plural = "избранные рецепты"

    def __str__(self):
        return f"{self.user} ♥ {self.recipe}"


class ShoppingCart(models.Model):
    """Список покупок"""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="in_shopping_carts",
        verbose_name="рецепт",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shopping_carts",
        verbose_name="пользователь",
    )

    class Meta:
        ordering = ("user", "recipe")
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"],
                name="unique_shopping_cart",
            ),
        ]
        verbose_name = "список покупок"
        verbose_name_plural = "списки покупок"

    def __str__(self):
        return f"{self.user} 🛒 {self.recipe}"
