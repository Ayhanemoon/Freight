from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from freight.api.v1.serializers import CustomerSerializer
from freight.constants import Roles
from freight.models import Customer, CustomerBranchMembership


class CustomerAPIAccessPermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        # This step only secures read access.
        # Customer creation/update/delete will be handled
        # after the onboarding workflow is finalized.
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            return False

        if user.is_superuser:
            return True

        return user.groups.filter(
            name__in=[
                Roles.CUSTOMER,
                Roles.BRANCH_MANAGER,
            ]
        ).exists()


class CustomerViewSet(ModelViewSet):
    queryset = Customer.objects.select_related("user").all()
    serializer_class = CustomerSerializer

    permission_classes = [
        IsAuthenticated,
        CustomerAPIAccessPermission,
    ]

    def get_queryset(self):
        user = self.request.user
        queryset = self.queryset

        # SuperAdmin: all customers.
        if user.is_superuser:
            return queryset

        # Customer: only their own customer profile.
        if user.groups.filter(name=Roles.CUSTOMER).exists():
            return queryset.filter(user=user)

        # BranchManager: only customers with an ACTIVE
        # membership in the manager's own branch.
        if user.groups.filter(name=Roles.BRANCH_MANAGER).exists():
            if not user.branch_id:
                return queryset.none()

            return queryset.filter(
                branch_memberships__branch_id=user.branch_id,
                branch_memberships__status=(
                    CustomerBranchMembership.Status.ACTIVE
                ),
            ).distinct()

        # All other roles: no customer visibility.
        return queryset.none()