from rest_framework import permissions

class IsStaffForCenter(permissions.BasePermission):
    """
    Пользователь с ролью STAFF может управлять только секциями и расписанием своего центра.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser or request.user.is_staff:
            return True

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
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated
