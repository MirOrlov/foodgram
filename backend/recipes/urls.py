from django.urls import path

from . import views

urlpatterns = [
    path('recipes/<int:recipe_id>/', views.redirect_to_recipe, name='recipe-short-link'),
]