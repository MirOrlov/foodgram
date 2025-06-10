from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.views import (
    UserViewSet,
    IngredientViewSet,
    RecipeViewSet,
TagViewSet,
)

router = DefaultRouter()
router.register("ingredients", IngredientViewSet)
router.register("recipes", RecipeViewSet)
router.register("users", UserViewSet)
router.register("tags", TagViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include('djoser.urls.authtoken')),
]
