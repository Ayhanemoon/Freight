from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from freight.models import InvoiceCharge

from .invoice import recalculate_invoice_total


def _validate_charge_amount(amount):
    if amount < 0:
        raise ValidationError(
            "Invoice charge amount cannot be negative."
        )


def _validate_invoice_access(*, invoice, user, permission):
    if user.is_superuser:
        return

    if not user.is_active:
        raise PermissionDenied(
            "User account is inactive."
        )

    if user.branch_id != invoice.order.branch_id:
        raise PermissionDenied(
            "You cannot manage invoice charges "
            "outside your branch."
        )

    if not user.has_perm(permission):
        raise PermissionDenied(
            "You do not have permission to manage invoice charges."
        )


@transaction.atomic
def create_invoice_charge(
    *,
    invoice,
    created_by,
    charge_type,
    amount,
    payer=None,
    description="",
):
    """
    Create an invoice charge and recalculate invoice total.
    """

    _validate_invoice_access(
        invoice=invoice,
        user=created_by,
        permission="freight.add_invoicecharge",
    )

    _validate_charge_amount(amount)

    if payer and payer not in {
        InvoiceCharge.Payer.SENDER,
        InvoiceCharge.Payer.RECEIVER,
    }:
        raise ValidationError(
            "Invalid payer."
        )

    charge = InvoiceCharge.objects.create(
        invoice=invoice,
        charge_type=charge_type,
        payer=payer,
        description=description,
        amount=amount,
    )

    recalculate_invoice_total(invoice)

    return charge


@transaction.atomic
def update_invoice_charge(
    *,
    charge,
    updated_by,
    charge_type=None,
    amount=None,
    payer=None,
    description=None,
):
    """
    Update an invoice charge and recalculate invoice total.
    """

    invoice = charge.invoice

    _validate_invoice_access(
        invoice=invoice,
        user=updated_by,
        permission="freight.change_invoicecharge",
    )

    if amount is not None:
        _validate_charge_amount(amount)
        charge.amount = amount

    if charge_type is not None:
        charge.charge_type = charge_type

    if payer is not None:
        if payer not in {
            InvoiceCharge.Payer.SENDER,
            InvoiceCharge.Payer.RECEIVER,
        }:
            raise ValidationError(
                "Invalid payer."
            )

        charge.payer = payer

    if description is not None:
        charge.description = description

    charge.save(
        update_fields=[
            "charge_type",
            "payer",
            "description",
            "amount",
        ]
    )

    recalculate_invoice_total(invoice)

    return charge


@transaction.atomic
def delete_invoice_charge(
    *,
    charge,
    deleted_by,
):
    """
    Delete an invoice charge and recalculate invoice total.
    """

    invoice = charge.invoice

    _validate_invoice_access(
        invoice=invoice,
        user=deleted_by,
        permission="freight.delete_invoicecharge",
    )

    charge.delete()

    recalculate_invoice_total(invoice)

    return invoice