from django.core.exceptions import ValidationError
from django.db import transaction

from freight.models.shipment_order import ShipmentOrder
from freight.services.shipment_order import change_order_status


@transaction.atomic
def receive_shipment_at_branch(
    *,
    order,
    received_by,
    note="",
):
    if order.status != ShipmentOrder.Status.COLLECTED:
        raise ValidationError(
            "Only collected shipments can be received at the branch."
        )

    if received_by.is_superuser:
        pass
    else:
        if received_by.branch_id != order.branch_id:
            raise ValidationError(
                "You can only receive shipments at your own branch."
            )

    change_order_status(
        order=order,
        new_status=ShipmentOrder.Status.RECEIVED_AT_BRANCH,
        changed_by=received_by,
        note=note or "Shipment received at branch.",
    )

    return order