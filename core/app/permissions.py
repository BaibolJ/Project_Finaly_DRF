from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Пользовательское разрешение, позволяющее редактировать или удалять комментарий только его автору.
    """

    def has_object_permission(self, request, view, obj):
        # Разрешения на чтение доступны любому запросу,
        # поэтому мы всегда разрешаем GET, HEAD или OPTIONS запросы.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Разрешения на запись доступны только автору комментария.
        return obj.user == request.user