from rest_framework import permissions

class IsAdminUserRole(permissions.BasePermission):
    """
    Allows access only to Admin users.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.role == 'ADMIN'))
        )

class IsStaffOrAdminUserRole(permissions.BasePermission):
    """
    Allows access to Staff and Admin users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
