from rest_framework.permissions import SAFE_METHODS, BasePermission


def es_root(user):
    """Return True only for authenticated superuser accounts."""
    return bool(user and user.is_authenticated and user.is_superuser)


class EsRootPermission(BasePermission):
    """Allow access exclusively to authenticated superuser accounts."""

    def has_permission(self, request, view):
        return es_root(request.user)


class IsAdminOrReadOnly(BasePermission):
    """Allow read access to authenticated clinical users and writes only to admins."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return bool(user.is_staff)
