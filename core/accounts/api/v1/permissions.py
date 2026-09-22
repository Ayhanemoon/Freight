from rest_framework.permissions import BasePermission


class CanViewUsers(BasePermission):
    message = "You do not have permission to view users."

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        return user.has_perm("accounts.view_user")

class CanCreateUsers(BasePermission):
    message = "You do not have permission to create users."

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        return user.has_perm("accounts.add_user")


class CanManageUsers(BasePermission):
    message = "You do not have permission to manage this user."

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        return user.has_perm("accounts.change_user")

    def has_object_permission(self, request, view, obj):
        user = request.user

        if user.is_superuser:
            return True

        return obj.branch_id == user.branch_id