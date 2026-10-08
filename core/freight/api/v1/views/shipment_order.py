from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from freight.api.v1.serializers import ShipmentOrderSerializer
from freight.models import (
    CustomerBranchMembership,
    ShipmentOrder,
)
from freight.permissions.capabilities import (
    has_shipment_order_access_capability,
    has_shipment_order_change_capability,
    has_shipment_order_create_capability,
    is_cargo_collector_user,
    is_customer_user,
    is_dispatcher_user,
)


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

        if not has_shipment_order_access_capability(user):
            return queryset.none()

        # SuperAdmin / global capability.
        if user.is_superuser:
            return queryset

        # Customer: own orders only.
        if is_customer_user(user):
            return queryset.filter(
                customer__user_id=user.id,
            )

        # CargoCollector: assigned collection orders only.
        if is_cargo_collector_user(user):
            return queryset.filter(
                collection_task__collector_id=user.id,
            )

        # Dispatcher: orders assigned through dispatch batches.
        if is_dispatcher_user(user):
            return queryset.filter(
                dispatch_items__batch__dispatcher_id=user.id,
            ).distinct()

        # Branch-scoped staff.
        if not user.branch_id:
            return queryset.none()

        return queryset.filter(
            branch_id=user.branch_id,
        )

    def perform_create(self, serializer):
        user = self.request.user

        if not has_shipment_order_create_capability(user):
            raise PermissionDenied(
                "You do not have permission to create shipment orders."
            )

        # SuperAdmin can create an order for any branch.
        if user.is_superuser:
            serializer.save(
                created_by=user,
            )
            return

        # Customer creates an order for one of their ACTIVE
        # CustomerBranchMembership records.
        if is_customer_user(user):
            try:
                customer = user.customer_profile
            except AttributeError:
                raise PermissionDenied(
                    "Customer profile is required to create a shipment order."
                )

            branch = serializer.validated_data.get("branch")

            if branch is None:
                raise PermissionDenied(
                    "A branch is required to create a shipment order."
                )

            has_active_membership = (
                CustomerBranchMembership.objects.filter(
                    customer=customer,
                    branch=branch,
                    status=CustomerBranchMembership.Status.ACTIVE,
                ).exists()
            )

            if not has_active_membership:
                raise PermissionDenied(
                    "Customer is not an active member of the selected branch."
                )

            serializer.save(
                customer=customer,
                branch=branch,
                created_by=user,
            )
            return

        # BranchManager capability is branch-scoped.
        if not user.branch_id:
            raise PermissionDenied(
                "Branch is required for shipment-order creation."
            )

        branch = serializer.validated_data.get("branch")

        if branch is None:
            raise PermissionDenied(
                "A branch is required to create a shipment order."
            )

        if branch.id != user.branch_id:
            raise PermissionDenied(
                "You cannot create an order for another branch."
            )

        customer = serializer.validated_data.get("customer")

        if customer is None:
            raise PermissionDenied(
                "Customer is required to create a shipment order."
            )

        customer_has_branch = CustomerBranchMembership.objects.filter(
            customer=customer,
            branch=branch,
            status=CustomerBranchMembership.Status.ACTIVE,
        ).exists()

        if not customer_has_branch:
            raise PermissionDenied(
                "Customer is not an active member of the selected branch."
            )

        serializer.save(
            created_by=user,
        )

    def perform_update(self, serializer):
        user = self.request.user
        instance = self.get_object()

        if not has_shipment_order_change_capability(user):
            raise PermissionDenied(
                "You do not have permission to modify shipment orders."
            )

        # Customer-specific ownership and lifecycle rules.
        if is_customer_user(user):
            if instance.customer.user_id != user.id:
                raise PermissionDenied(
                    "You cannot modify another customer's order."
                )

            if instance.status != ShipmentOrder.Status.DRAFT:
                raise PermissionDenied(
                    "Only draft shipment orders can be modified."
                )

            # Customer cannot change ownership or branch.
            serializer.save(
                customer=instance.customer,
                branch=instance.branch,
                created_by=instance.created_by,
            )
            return

        # Branch/object scope is already enforced by get_queryset().
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        raise PermissionDenied(
            "Shipment orders cannot be deleted. "
            "Use the cancellation workflow instead."
        )