from django.urls import path

from . import views

urlpatterns = [
    path('recipes/<int:pk>/', views.redirect_recipe, name='redirect_recipe'),
]
