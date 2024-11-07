from rest_framework import permissions

class IsStaffForCenter(permissions.BasePermission):
    """
    Пользователь с ролью STAFF может управлять только секциями и расписанием своего центра.
    """

    def has_object_permission(self, request, view, obj):
        # Если пользователь является суперпользователем (админом), предоставить все права
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Если пользователь STAFF, проверить, привязан ли он к центру
        if request.user.role == 'STAFF':
            return obj.center.users.filter(id=request.user.id).exists()

        return False

from rest_framework.permissions import BasePermission, SAFE_METHODS

class AllowAnyForGETOtherwiseIsAuthenticated(BasePermission):
    """
    Разрешает неаутентифицированный доступ для GET-запросов,
    но требует аутентификацию для всех других запросов.
    """
    def has_permission(self, request, view):
        # Разрешаем доступ для неаутентифицированных GET-запросов
        if request.method in SAFE_METHODS:
            return True
        # Для всех других методов требуется аутентификация
        return request.user and request.user.is_authenticated
