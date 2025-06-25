from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAuthorOrReadOnly(BasePermission):
    """
    Разрешает полный доступ только автору объекта.
    Для всех остальных - только чтение.
    """

    def has_permission(self, request, view):
        """Общая проверка разрешения для всего эндпоинта"""
        return request.method in SAFE_METHODS or request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Проверка разрешений для конкретного объекта"""
        return (
            request.method in SAFE_METHODS or
            obj.author == request.user
        )