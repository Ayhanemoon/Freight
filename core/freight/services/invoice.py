from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from freight.models import (
    Invoice,
    InvoiceCharge,
    InvoiceParcel,
    ShipmentOrder,
    ShipmentStatusHistory,
)


@transaction.atomic
def create_invoice(
    *,
    order,
    operator,
    invoice_number,
    issued_at=None,
    charges=None,
    parcels=None,
    notes="",
):
    """
    Create an invoice for a shipment order.

    Expected order status:
        RECEIVED_AT_BRANCH

    On success:
        - Invoice is created
        - InvoiceParcel snapshot records are created
        - InvoiceCharge records are created
        - Invoice.total_cost is calculated
        - ShipmentOrder -> INVOICE_REGISTERED
        - ShipmentStatusHistory is created
    """

    _validate_operator_access(
        order=order,
        operator=operator,
    )

    _validate_order_status(order)

    if Invoice.objects.filter(order=order).exists():
        raise ValidationError(
            "This shipment order already has an invoice."
        )

    if Invoice.objects.filter(
        invoice_number=invoice_number
    ).exists():
        raise ValidationError(
            "An invoice with this invoice number already exists."
        )

    issued_at = issued_at or timezone.now()

    charges = charges or []
    parcels = parcels or []

    _validate_parcels(
        order=order,
        parcels=parcels,
    )

    total_cost = _calculate_total(charges)

    invoice = Invoice.objects.create(
        order=order,
        invoice_number=invoice_number,
        issued_at=issued_at,
        operator=operator,

        # Customer snapshot
        customer_name=order.customer.display_name,
        customer_mobile=str(order.customer.user.mobile),
        customer_address=order.sender_address,

        # Receiver snapshot
        receiver_name=order.receiver_name,
        receiver_mobile=order.receiver_mobile,
        receiver_address=order.receiver_address,

        total_cost=total_cost,
        notes=notes,
    )

    _create_invoice_parcels(
        invoice=invoice,
        parcels=parcels,
    )

    _create_invoice_charges(
        invoice=invoice,
        charges=charges,
    )

    previous_status = order.status

    order.status = ShipmentOrder.Status.INVOICE_REGISTERED
    order.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    ShipmentStatusHistory.objects.create(
        shipment=order,
        from_status=previous_status,
        to_status=ShipmentOrder.Status.INVOICE_REGISTERED,
        changed_by=operator,
        note=f"Invoice {invoice.invoice_number} registered.",
    )

    return invoice


def _validate_operator_access(*, order, operator):
    if operator.is_superuser:
        return

    if not operator.is_active:
        raise PermissionDenied(
            "Operator account is inactive."
        )

    if operator.branch_id != order.branch_id:
        raise PermissionDenied(
            "You cannot create an invoice for an order outside your branch."
        )

    if not operator.has_perm("freight.add_invoice"):
        raise PermissionDenied(
            "You do not have permission to create invoices."
        )


def _validate_order_status(order):
    if order.status != ShipmentOrder.Status.RECEIVED_AT_BRANCH:
        raise ValidationError(
            "Invoice can only be created after the shipment "
            "has been received at the branch."
        )


def _validate_parcels(*, order, parcels):
    if not parcels:
        raise ValidationError(
            "At least one parcel is required for an invoice."
        )

    parcel_ids = {
        item["parcel"].id
        for item in parcels
    }

    order_parcel_ids = set(
        order.parcels.values_list(
            "id",
            flat=True,
        )
    )

    invalid_parcels = parcel_ids - order_parcel_ids

    if invalid_parcels:
        raise ValidationError(
            "One or more parcels do not belong to this shipment order."
        )

    if len(parcel_ids) != len(parcels):
        raise ValidationError(
            "A parcel cannot be added to the same invoice more than once."
        )


def _calculate_total(charges):
    total = Decimal("0")

    for charge in charges:
        amount = charge["amount"]

        if amount < 0:
            raise ValidationError(
                "Invoice charge amount cannot be negative."
            )

        total += amount

    return total


def _create_invoice_charges(*, invoice, charges):
    for charge in charges:
        InvoiceCharge.objects.create(
            invoice=invoice,
            charge_type=charge["charge_type"],
            payer=charge.get("payer"),
            description=charge.get("description", ""),
            amount=charge["amount"],
        )


def _create_invoice_parcels(*, invoice, parcels):
    for item in parcels:
        parcel = item["parcel"]

        InvoiceParcel.objects.create(
            invoice=invoice,
            parcel=parcel,
            parcel_number=parcel.parcel_number,
            parcel_name=item.get(
                "parcel_name",
                "",
            ),
            parcel_type=item.get(
                "parcel_type",
                "",
            ),
            quantity=item.get(
                "quantity",
                1,
            ),
        )