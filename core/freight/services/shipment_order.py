from django.core.exceptions import ValidationError
from django.db import transaction

from freight.models import ShipmentOrder, ShipmentStatusHistory


ALLOWED_ORDER_TRANSITIONS = {
    ShipmentOrder.Status.DRAFT: {
        ShipmentOrder.Status.SUBMITTED,
        ShipmentOrder.Status.CANCELLED,
    },

    ShipmentOrder.Status.SUBMITTED: {
        ShipmentOrder.Status.OPERATOR_REVIEW,
        ShipmentOrder.Status.CANCELLED,
        ShipmentOrder.Status.REJECTED,
    },

    ShipmentOrder.Status.OPERATOR_REVIEW: {
        ShipmentOrder.Status.APPROVED_FOR_COLLECTION,
        ShipmentOrder.Status.REJECTED,
        ShipmentOrder.Status.CANCELLED,
    },

    ShipmentOrder.Status.APPROVED_FOR_COLLECTION: {
        ShipmentOrder.Status.COLLECTED,
        ShipmentOrder.Status.CANCELLED,
    },

    ShipmentOrder.Status.COLLECTED: {
        ShipmentOrder.Status.RECEIVED_AT_BRANCH,
        ShipmentOrder.Status.CANCELLED,
    },

    ShipmentOrder.Status.RECEIVED_AT_BRANCH: {
        ShipmentOrder.Status.INVOICE_REGISTERED,
        ShipmentOrder.Status.CANCELLED,
    },

    ShipmentOrder.Status.INVOICE_REGISTERED: {
        ShipmentOrder.Status.READY_FOR_DISPATCH,
        ShipmentOrder.Status.CANCELLED,
    },

    ShipmentOrder.Status.READY_FOR_DISPATCH: {
        ShipmentOrder.Status.DISPATCHED_TO_FREIGHT,
        ShipmentOrder.Status.CANCELLED,
    },

    ShipmentOrder.Status.DISPATCHED_TO_FREIGHT: {
        ShipmentOrder.Status.HANDOVER_PENDING_APPROVAL,
    },

    ShipmentOrder.Status.HANDOVER_PENDING_APPROVAL: {
        ShipmentOrder.Status.HANDOVER_APPROVED,
        ShipmentOrder.Status.REJECTED,
    },

    ShipmentOrder.Status.HANDOVER_APPROVED: {
        ShipmentOrder.Status.COMPLETED,
    },

    ShipmentOrder.Status.COMPLETED: set(),

    ShipmentOrder.Status.CANCELLED: set(),

    ShipmentOrder.Status.REJECTED: set(),
}


@transaction.atomic
def change_order_status(
    *,
    order,
    new_status,
    changed_by=None,
    note="",
):
    current_status = order.status

    if current_status == new_status:
        raise ValidationError(
            f"Order is already in {current_status} status."
        )

    allowed_statuses = ALLOWED_ORDER_TRANSITIONS.get(
        current_status,
        set(),
    )

    if new_status not in allowed_statuses:
        raise ValidationError(
            f"Cannot change order status from "
            f"{current_status} to {new_status}."
        )

    previous_status = order.status

    order.status = new_status

    order.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    ShipmentStatusHistory.objects.create(
        shipment=order,
        from_status=previous_status,
        to_status=new_status,
        changed_by=changed_by,
        note=note,
    )

    return order