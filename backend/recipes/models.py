from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import MinValueValidator
from django.conf import settings

from foodgram import consts


class User(AbstractUser):
    """Кастомная модель пользователя с дополнительными полями."""

    email = models.EmailField(
        verbose_name="Электронная почта",
        unique=True,
    )
    username = models.CharField(
        verbose_name="Логин",
        max_length=consts.MAX_USER_NAME,
        unique=True,
        validators=[UnicodeUsernameValidator()],
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
        default="",
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
        constraints = [
            models.UniqueConstraint(
                fields=["name", "measurement_unit"],
                name="unique_ingredient",
            ),
        ]

    def __str__(self):
        return f"{self.name}, {self.measurement_unit}"


class Recipe(models.Model):
    """Основная модель рецептов."""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Автор рецепта",
        on_delete=models.CASCADE,
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
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name="Теги",
    )

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ("name",)
        default_related_name = "recipes"

    def __str__(self):
        return f"{self.name} (автор: {self.author.username})"


class RecipeIngredient(models.Model):
    """Промежуточная модель для связи рецептов и ингредиентов."""

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
        default_related_name = "recipe_ingredients"

    def __str__(self):
        return (
            f"{self.ingredient.name} - {self.amount} "
            f"{self.ingredient.measurement_unit}"
        )


class UserRecipeRelation(models.Model):
    """Абстрактная модель для связи пользователей и рецептов."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"],
                name="unique_%(class)s",
            ),
        ]


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
        return (
            f"{self.user.username} подписан на "
            f"{self.subscribed_to.username}"
        )


class Favorite(UserRecipeRelation):
    """Модель избранных рецептов пользователей."""

    class Meta(UserRecipeRelation.Meta):
        verbose_name = "Избранное"
        verbose_name_plural = "Избранные рецепты"
        default_related_name = "favorites"

    def __str__(self):
        return f"{self.user.username} - {self.recipe.name}"


class ShoppingCart(UserRecipeRelation):
    """Модель списка покупок пользователей."""

    class Meta(UserRecipeRelation.Meta):
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"
        default_related_name = "shopping_carts"

    def __str__(self):
        return f"Корзина {self.user.username}: {self.recipe.name}"
