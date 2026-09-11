# models/dispatch_freight_assignment.py

from django.conf import settings
from django.db import models

from freight.models import DispatchOrder, FreightCompany


class DispatchFreightAssignment(models.Model):

    class Status(models.TextChoices):
        DISPATCHING = "dispatching", "Dispatching"
        PENDING_APPROVAL = "pending_approval", "Pending Approval"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled"

    class Payer(models.TextChoices):
        SENDER = "sender", "Sender"
        RECEIVER = "receiver", "Receiver"

    dispatch_order = models.ForeignKey(
        DispatchOrder,
        on_delete=models.CASCADE,
        related_name="freight_assignments",
    )

    freight_company = models.ForeignKey(
        FreightCompany,
        on_delete=models.PROTECT,
        related_name="dispatch_assignments",
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.DISPATCHING,
    )

    payer = models.CharField(
        max_length=20,
        choices=Payer.choices,
    )

    freight_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )

    rejection_reason = models.TextField(
        blank=True,
    )

    freight_invoice_number = models.CharField(
        max_length=100,
        blank=True,
    )

    freight_invoice_file = models.FileField(
        upload_to="freight_invoices/",
        null=True,
        blank=True,
    )

    notes = models.TextField(
        blank=True,
    )

    assigned_at = models.DateTimeField(
        auto_now_add=True,
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_freight_assignments",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return (
            f"{self.dispatch_order.order.tracking_code} - "
            f"{self.freight_company.name}"
        )