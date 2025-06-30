from io import BytesIO
from datetime import datetime

from django.core.files.storage import default_storage
from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models.functions import Lower
from django.core.exceptions import ValidationError
from rest_framework import (
    decorators,
    filters,
    permissions,
    status,
    viewsets,
    response
)
from django.urls import reverse
from djoser.views import UserViewSet as DjoserUserViewSet

from recipes.models import (
    Recipe,
    RecipeIngredient,
    Favorite,
    Ingredient,
    User,
    Subscription,
    ShoppingCart,
    Tag,
)
from api.filters import IngredientSearchFilter, CustomRecipeFilter
from api.paginations import CustomPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    AvatarSerializer,
    IngredientSerializer,
    RecipeSerializer,
    UserSerializer,
    UserSubscriptionSerializer,
    RecipeShortSerializer,
    TagSerializer,
    FavoriteSerializer,
    ShoppingCartSerializer
)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all().order_by(Lower('name'))
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientSearchFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """
    Вьюсет для работы с рецептами.
    Поддерживает создание, просмотр, редактирование и удаление рецептов,
    а также дополнительные действия: избранное, список покупок и скачивание списка.
    """
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
        IsAuthorOrReadOnly,
    ]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = CustomRecipeFilter

    def perform_create(self, serializer):
        """Автоматически устанавливает автора при создании рецепта."""
        serializer.save(author=self.request.user)

    @staticmethod
    def _add_relation(request, pk, serializer_class, model, relation_name):
        """Общий метод для добавления связи (избранное/корзина)."""
        recipe = get_object_or_404(Recipe, id=pk)

        serializer = serializer_class(
            data={'recipe': recipe.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return response.Response(
            RecipeShortSerializer(recipe, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    @staticmethod
    def _remove_relation(request, pk, model):
        """Общий метод для удаления связи (избранное/корзина)."""
        recipe = get_object_or_404(Recipe, pk=pk)
        deleted_count, _ = model.objects.filter(
            user=request.user,
            recipe=recipe
        ).delete()

        if deleted_count == 0:
            return response.Response(
                {'errors': f'Рецепт не найден в {model._meta.verbose_name}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return response.Response(status=status.HTTP_204_NO_CONTENT)

    @decorators.action(
        detail=True,
        methods=["post"],
        url_name="favorite",
        permission_classes=[permissions.IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        return self._add_relation(
            request, pk, FavoriteSerializer, Favorite, 'избранном'
        )

    @favorite.mapping.delete
    def remove_from_favorite(self, request, pk=None):
        return self._remove_relation(request, pk, Favorite)

    @decorators.action(
        detail=True,
        methods=["post"],
        url_name="shopping_cart",
        permission_classes=[permissions.IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        return self._add_relation(
            request, pk, ShoppingCartSerializer, ShoppingCart, 'корзине'
        )

    @shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk=None):
        return self._remove_relation(request, pk, ShoppingCart)

    @decorators.action(
        detail=True,
        methods=["get"],
        url_path="get-link"
    )
    def link(self, request, pk=None):
        """
        Генерирует короткую ссылку на рецепт.
        Возвращает URL для перенаправления к рецепту.
        """
        get_object_or_404(Recipe, id=pk)
        short_url = request.build_absolute_uri(
            reverse('redirect_recipe', kwargs={'pk': pk})
        )
        return response.Response({"short-link": short_url})

    @decorators.action(
        detail=False,
        methods=["get"],
        url_path="download_shopping_cart",
        permission_classes=[permissions.IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        """
        Генерирует и возвращает текстовый файл со списком покупок
        для всех рецептов в корзине пользователя.
        """
        recipes = Recipe.objects.filter(
            shopping_carts__user=request.user
        ).prefetch_related('recipe_ingredients__ingredient', 'author')

        ingredients = (
            RecipeIngredient.objects.filter(recipe__in=recipes)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )

        report_content = [
            f"Список покупок",
            f"Дата составления: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            f"Всего рецептов: {len(recipes)}",
            f"Всего ингредиентов: {len(ingredients)}",
            "",
            "Список продуктов:",
            *[
                f"{idx}. {ing['ingredient__name'].capitalize()} - "
                f"{ing['total_amount']} {ing['ingredient__measurement_unit']}"
                for idx, ing in enumerate(ingredients, start=1)
            ],
            "",
            "Рецепты:",
            *[
                f"- {recipe.name} (автор: {recipe.author.username})"
                for recipe in recipes
            ]
        ]

        buffer = BytesIO('\n'.join(report_content).encode('utf-8'))
        return FileResponse(
            buffer,
            as_attachment=True,
            filename=f"shopping_list_{datetime.now().strftime('%Y%m%d')}.txt",
            content_type='text/plain'
        )


class UserViewSet(DjoserUserViewSet):
    pagination_class = CustomPagination

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return UserSerializer
        return super().get_serializer_class()

    @decorators.action(
        detail=False,
        methods=["get"],
        url_path="me",
        permission_classes=[permissions.IsAuthenticated],
    )
    def me(self, request, *args, **kwargs):
        serializer = UserSerializer(
            request.user, context={"request": request}
        )
        return response.Response(serializer.data)

    @decorators.action(
        detail=False,
        methods=["put"],
        permission_classes=[permissions.IsAuthenticated],
        url_path="me/avatar",
    )
    def upload_avatar(self, request, *args, **kwargs):
        """Загружает новый аватар для текущего пользователя."""
        serializer = AvatarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        request.user.avatar = serializer.validated_data["avatar"]
        request.user.save()

        return response.Response(
            {"avatar": request.user.avatar.url},
            status=status.HTTP_200_OK
        )

    @upload_avatar.mapping.delete
    def delete_avatar(self, request, *args, **kwargs):
        """Полностью удаляет аватар пользователя с диска и из БД"""
        user = request.user

        if not user.avatar:
            return response.Response(
                {'detail': 'Аватар не найден'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Получаем путь к файлу до удаления
        avatar_path = user.avatar.path

        try:
            # Удаляем файл с диска
            if default_storage.exists(avatar_path):
                default_storage.delete(avatar_path)

            # Обновляем запись в БД
            user.avatar = None
            user.save()

            return response.Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            return response.Response(
                {'detail': f'Ошибка при удалении аватара: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @decorators.action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[permissions.IsAuthenticated],
        url_path="subscribe",
    )
    def subscribe(self, request, *args, **kwargs):
        author = self.get_object()
        user = request.user
        if request.method == 'POST':
            return self._create_subscription(user, author, request)
        return self._delete_subscription(user, author)

    def _create_subscription(self, user, author, request):
        """Создает подписку на пользователя"""
        serializer = UserSubscriptionSerializer(
            data={},
            context={
                'request': request,
                'view': self
            }
        )

        if not serializer.is_valid():
            return response.Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        subscription = Subscription(user=user, subscribed_to=author)
        subscription.save()

        data = UserSubscriptionSerializer(
            author, context={'request': request}
        ).data
        return response.Response(data, status=status.HTTP_201_CREATED)

    def _delete_subscription(self, user, author):
        """Удаляет подписку на пользователя"""
        deleted_count, _ = Subscription.objects.filter(
            user=user,
            subscribed_to=author
        ).delete()

        if not deleted_count:
            return response.Response(
                {'errors': 'Подписка не найдена.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return response.Response(status=status.HTTP_204_NO_CONTENT)

    @decorators.action(
        detail=False,
        methods=["get"],
        permission_classes=[permissions.IsAuthenticated],
        url_path="subscriptions",
    )
    def subscriptions(self, request, *args, **kwargs):
        user = request.user
        queryset = User.objects.filter(subscribers__user=user)
        pages = self.paginate_queryset(queryset)
        serializer = UserSubscriptionSerializer(
            pages, many=True, context={"request": request}
        )
        return self.get_paginated_response(serializer.data)
