from rest_framework.permissions import BasePermission


class CanViewUsers(BasePermission):
    message = "You do not have permission to view users."

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        return user.groups.filter(
            permissions__codename="view_user",
            permissions__content_type__app_label="accounts",
        ).exists()