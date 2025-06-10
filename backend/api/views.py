from io import BytesIO
from datetime import datetime

from django.core.files.storage import default_storage
from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models.functions import Lower
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
from api.filters import IngredientFilter, RecipeFilter
from api.paginations import Pagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    AvatarSerializer,
    IngredientSerializer,
    RecipeSerializer,
    UserSerializer,
    UserSubscriptionSerializer,
    RecipeShortSerializer,
    TagSerializer,
)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all().order_by(Lower('name'))
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = IngredientFilter

class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None



class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
        IsAuthorOrReadOnly,
    ]
    pagination_class = Pagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = RecipeFilter

    @decorators.action(detail=True, methods=["get"], url_path="get-link")
    def link(self, request, pk=None):
        get_object_or_404(Recipe, id=pk)
        short_url = request.build_absolute_uri(
            reverse('recipe-short-link', kwargs={'recipe_id': pk})
        )
        return response.Response({"short-link": short_url})

    @decorators.action(
        detail=True,
        methods=["post"],
        url_name="favorite",
        permission_classes=[permissions.IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        return self._add_to_relation(request, pk, Favorite, RecipeShortSerializer)

    @decorators.action(
        detail=True,
        methods=["post"],
        url_name="shopping_cart",
        permission_classes=[permissions.IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        return self._add_to_relation(request, pk, ShoppingCart, RecipeShortSerializer)

    def _add_to_relation(self, request, pk, model, serializer_class):
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user

        instance, created = model.objects.get_or_create(user=user, recipe=recipe)

        if not created:
            model_name = model._meta.verbose_name
            return response.Response(
                {"errors": f"Рецепт '{recipe.name}' уже в {model_name}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = serializer_class(recipe, context={'request': request})
        return response.Response(serializer.data, status=status.HTTP_201_CREATED)

    def _remove_from_relation(self, request, pk, model):
        get_object_or_404(model, user=request.user, recipe_id=pk).delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    @favorite.mapping.delete
    def remove_from_favorite(self, request, pk=None):
        return self._remove_from_relation(request, pk, Favorite)

    @shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk=None):
        return self._remove_from_relation(request, pk, ShoppingCart)

    @decorators.action(
        detail=False,
        methods=["get"],
        url_path="download_shopping_cart",
        permission_classes=[permissions.IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        recipes = Recipe.objects.filter(
            in_shopping_carts__user=request.user
        ).prefetch_related('recipe_ingredients__ingredient', 'author')
        ingredients = (
            RecipeIngredient.objects.filter(recipe__in=recipes)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )
        parts = [
            f"Список покупок\n"
            f"Дата составления: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            f"Всего рецептов: {len(recipes)}\n"
            f"Всего ингредиентов: {len(ingredients)}\n",

            "Список продуктов:",
            *[
                f"{idx}. {ing['ingredient__name'].capitalize()} - "
                f"{ing['total_amount']} {ing['ingredient__measurement_unit']}"
                for idx, ing in enumerate(ingredients, start=1)
            ],

            "\nРецепты:",
            *[
                f"- {recipe.name} (автор: {recipe.author.username})"
                for recipe in recipes
            ]
        ]

        report_text = '\n'.join(parts)

        buffer = BytesIO(report_text.encode('utf-8'))
        return FileResponse(
            buffer,
            as_attachment=True,
            filename=f"shopping_list_{datetime.now().strftime('%Y%m%d')}.txt",
            content_type='text/plain'
        )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class UserViewSet(DjoserUserViewSet):
    pagination_class = Pagination

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
        methods=["put", "delete"],
        permission_classes=[permissions.IsAuthenticated],
        url_path="me/avatar",
    )
    def avatar(self, request, *args, **kwargs):
        user = request.user

        if request.method == "PUT":
            serializer = AvatarSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            avatar = serializer.validated_data["avatar"]
            user.avatar = avatar
            user.save()
            return response.Response(
                {"avatar": user.avatar.url}, status=status.HTTP_200_OK
            )

        if user.avatar:
            if default_storage.exists(user.avatar.name):
                default_storage.delete(user.avatar.name)
            user.avatar = None
            user.save()
        return response.Response(status=status.HTTP_204_NO_CONTENT)

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
            if user == author:
                return response.Response(
                    {'errors': 'Нельзя подписаться на самого себя.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            _, created = Subscription.objects.get_or_create(
                user=user, subscribed_to=author
            )
            if not created:
                return response.Response(
                    {'errors': f'Вы уже подписаны на пользователя {author.username}.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            data = UserSubscriptionSerializer(
                author, context={'request': request}
            ).data
            return response.Response(data, status=status.HTTP_201_CREATED)
        get_object_or_404(
            Subscription, user=user, subscribed_to=author
        ).delete()
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
