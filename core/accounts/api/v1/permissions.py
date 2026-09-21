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

class CanCreateUsers(BasePermission):
    message = "You do not have permission to create users."

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        return user.groups.filter(
            permissions__codename="add_user",
            permissions__content_type__app_label="accounts",
        ).exists()


class CanManageUsers(BasePermission):
    message = "You do not have permission to manage this user."

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        return user.groups.filter(
            permissions__codename="change_user",
            permissions__content_type__app_label="accounts",
        ).exists()

    def has_object_permission(self, request, view, obj):
        user = request.user

        if user.is_superuser:
            return True

        return obj.branch_id == user.branch_id