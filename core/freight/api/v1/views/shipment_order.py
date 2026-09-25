from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from freight.api.v1.serializers import ShipmentOrderSerializer
from freight.constants.roles import Roles
from freight.models import ShipmentOrder


class ShipmentOrderViewSet(ModelViewSet):
    serializer_class = ShipmentOrderSerializer
    permission_classes = [IsAuthenticated]

    queryset = (
        ShipmentOrder.objects
        .select_related(
            "branch",
            "customer",
            "customer__user",
            "preferred_freight_company",
            "created_by",
        )
        .prefetch_related("parcels")
        .all()
    )

    def get_queryset(self):
        user = self.request.user
        queryset = self.queryset

        # SuperAdmin has global access.
        if user.is_superuser:
            return queryset

        # Customer can only see their own orders.
        if user.groups.filter(name=Roles.CUSTOMER).exists():
            return queryset.filter(customer__user=user)

        # All other authenticated users are branch-scoped.
        if not user.branch_id:
            return queryset.none()

        return queryset.filter(branch_id=user.branch_id)

    def perform_create(self, serializer):
        user = self.request.user

        is_super_admin = user.is_superuser
        is_branch_manager = user.groups.filter(
            name=Roles.BRANCH_MANAGER
        ).exists()
        is_customer = user.groups.filter(
            name=Roles.CUSTOMER
        ).exists()

        if not (
            is_super_admin
            or is_branch_manager
            or is_customer
        ):
            raise PermissionDenied(
                "You do not have permission to create shipment orders."
            )

        if is_customer and not is_super_admin:
            try:
                customer = user.customer_profile
            except AttributeError:
                raise PermissionDenied(
                    "Customer profile is required to create a shipment order."
                )

            if not user.branch_id:
                raise PermissionDenied(
                    "Customer must belong to a branch."
                )

            # Customer cannot choose another customer or branch.
            serializer.save(
                customer=customer,
                branch_id=user.branch_id,
                created_by=user,
            )
            return

        # SuperAdmin may create globally.
        if is_super_admin:
            serializer.save(created_by=user)
            return

        # BranchManager must create inside their own branch.
        if serializer.validated_data["branch"].id != user.branch_id:
            raise PermissionDenied(
                "You cannot create an order for another branch."
            )

        serializer.save(created_by=user)

    def perform_update(self, serializer):
        user = self.request.user
        instance = self.get_object()

        is_customer = user.groups.filter(
            name=Roles.CUSTOMER
        ).exists()

        # Customer may only edit their own DRAFT order.
        if is_customer and not user.is_superuser:
            if instance.customer.user_id != user.id:
                raise PermissionDenied(
                    "You cannot modify another customer's order."
                )

            if instance.status != ShipmentOrder.Status.DRAFT:
                raise PermissionDenied(
                    "Only draft shipment orders can be modified."
                )

            # Customer must never change ownership/scope.
            serializer.save(
                customer=instance.customer,
                branch=instance.branch,
                created_by=instance.created_by,
            )
            return

        # Staff can only modify objects returned by get_queryset(),
        # therefore branch isolation is already enforced.
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        # Shipment orders should follow the cancellation lifecycle.
        # Hard deletion would destroy operational/audit history.
        raise PermissionDenied(
            "Shipment orders cannot be deleted. "
            "Use the cancellation workflow instead."
        )