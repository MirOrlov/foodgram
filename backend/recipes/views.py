from django.shortcuts import redirect
from django.http import Http404

from recipes.models import Recipe


def redirect_recipe(request, pk):
    if not Recipe.objects.filter(pk=pk).exists():
        raise Http404
    return redirect(f'recipes/{pk}/')
