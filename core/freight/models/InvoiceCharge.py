from django.db import models

from freight.models import Invoice


class InvoiceCharge(models.Model):

    class ChargeType(models.TextChoices):
        FREIGHT = "freight", "Freight"
        INSURANCE = "insurance", "Insurance"
        CRANE_LOADING = "crane_loading", "Crane / Loading"
        BRANCH = "branch", "Branch"
        OTHER = "other", "Other"

    class Payer(models.TextChoices):
        SENDER = "sender", "Sender"
        RECEIVER = "receiver", "Receiver"

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="charges",
    )

    charge_type = models.CharField(
        max_length=30,
        choices=ChargeType.choices,
    )

    payer = models.CharField(
        max_length=20,
        choices=Payer.choices,
        null=True,
        blank=True,
    )

    description = models.CharField(
        max_length=255,
        blank=True,
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return (
            f"{self.invoice.invoice_number} - "
            f"{self.get_charge_type_display()}"
        )