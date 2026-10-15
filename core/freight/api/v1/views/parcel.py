from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from freight.api.v1.serializers import ParcelSerializer
from freight.models import Parcel, ShipmentOrder
from freight.permissions.capabilities import (
    has_any_permission,
    has_branch_admin_capability,
    is_cargo_collector_user,
    is_customer_user,
)


PRE_COLLECTION_STATUSES = {
    ShipmentOrder.Status.DRAFT,
    ShipmentOrder.Status.SUBMITTED,
    ShipmentOrder.Status.OPERATOR_REVIEW,
    ShipmentOrder.Status.APPROVED_FOR_COLLECTION,
}


def can_access_parcels(user):
    if has_branch_admin_capability(user):
        return True

    if is_customer_user(user) or is_cargo_collector_user(user):
        return True

    return has_any_permission(
        user,
        "freight.view_parcel",
        "freight.add_parcel",
        "freight.change_parcel",
        "freight.delete_parcel",
        "freight.verify_collection_task",
    )


def can_manage_declared_parcels(user, action):
    if has_branch_admin_capability(user):
        return True

    # CargoCollectors verify parcels through their assigned collection
    # task; they do not edit declared data through this generic endpoint.
    if is_cargo_collector_user(user):
        return False

    if action == "delete":
        return has_any_permission(user, "freight.delete_parcel")

    if action == "create":
        permissions = (
            "freight.add_parcel",
            "freight.verify_collection_task",
        )
    elif action == "update":
        permissions = (
            "freight.change_parcel",
            "freight.verify_collection_task",
        )
    else:
        return False

    return has_any_permission(user, *permissions)


class ParcelViewSet(ModelViewSet):
    serializer_class = ParcelSerializer
    permission_classes = [IsAuthenticated]

    queryset = (
        Parcel.objects
        .select_related(
            "order",
            "order__branch",
            "order__customer",
            "verified_by",
        )
        .all()
    )

    def get_queryset(self):
        user = self.request.user
        queryset = self.queryset

        if not can_access_parcels(user):
            return queryset.none()

        if user.is_superuser:
            return queryset

        if is_customer_user(user):
            return queryset.filter(order__customer__user_id=user.id)

        if is_cargo_collector_user(user):
            return queryset.filter(
                order__collection_task__collector_id=user.id,
            )

        if not user.branch_id:
            return queryset.none()

        else:
            queryset = queryset.filter(
                order__branch_id=user.branch_id,
            )

        # Optionally filter the accessible parcels by shipment order.
        order_id = self.request.query_params.get("order")

        if order_id:
            try:
                order_id = int(order_id)
            except (TypeError, ValueError):
                

                raise ValidationError({
                    "order": "Must be a valid shipment-order ID."
                })

            if order_id <= 0:

                raise ValidationError({
                    "order": "Must be a positive shipment-order ID."
                })

            queryset = queryset.filter(order_id=order_id)

        return queryset

    def _check_order_scope(self, order):
        user = self.request.user

        if user.is_superuser:
            return

        if is_customer_user(user):
            if order.customer.user_id != user.id:
                raise PermissionDenied(
                    "You cannot manage parcels for another customer's order."
                )
            return

        if is_cargo_collector_user(user):
            raise PermissionDenied(
                "Cargo collectors must use the collection verification workflow."
            )

        if not user.branch_id or order.branch_id != user.branch_id:
            raise PermissionDenied(
                "You cannot manage parcels for another branch."
            )

    def _check_order_lifecycle(self, order):
        if order.status not in PRE_COLLECTION_STATUSES:
            raise PermissionDenied(
                "Declared parcel data cannot be changed at this order stage."
            )

    def perform_create(self, serializer):
        user = self.request.user
        order = serializer.validated_data["order"]

        self._check_order_scope(order)

        if is_customer_user(user):
            if order.status != ShipmentOrder.Status.DRAFT:
                raise PermissionDenied(
                    "Customers can add parcels only to draft orders."
                )
        else:
            if not can_manage_declared_parcels(user, "create"):
                raise PermissionDenied(
                    "You do not have permission to add parcels."
                )

            self._check_order_lifecycle(order)

        serializer.save()

    def perform_update(self, serializer):
        user = self.request.user
        order = serializer.instance.order

        self._check_order_scope(order)

        if is_customer_user(user):
            if order.status != ShipmentOrder.Status.DRAFT:
                raise PermissionDenied(
                    "Customers can modify parcels only on draft orders."
                )
        else:
            if not can_manage_declared_parcels(user, "update"):
                raise PermissionDenied(
                    "You do not have permission to modify declared parcel data."
                )

            self._check_order_lifecycle(order)

        serializer.save()

    def destroy(self, request, *args, **kwargs):
        parcel = self.get_object()
        order = parcel.order
        user = request.user

        # Superusers follow the staff path, not customer restrictions.
        if is_customer_user(user) and not user.is_superuser:
            self._check_order_scope(order)

            if order.status != ShipmentOrder.Status.DRAFT:
                raise PermissionDenied(
                    "Customers can delete parcels only from draft orders."
                )
        else:
            self._check_order_scope(order)

            if not can_manage_declared_parcels(user, "delete"):
                raise PermissionDenied(
                    "You do not have permission to delete parcels."
                )

            self._check_order_lifecycle(order)

        self.perform_destroy(parcel)
        return Response(status=status.HTTP_204_NO_CONTENT)