from django.conf import settings
from django.db import models

from freight.models import Branch


class DispatchBatch(models.Model):

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        READY = "ready", "Ready for Dispatch"
        ASSIGNED = "assigned", "Assigned"
        IN_PROGRESS = "in_progress", "In Progress"
        DELIVERED = "delivered", "Delivered"
        PENDING_APPROVAL = "pending_approval", "Pending Approval"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled"

    branch = models.ForeignKey(
        Branch,
        on_delete=models.PROTECT,
        related_name="dispatch_batches",
    )

    dispatcher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="dispatch_batches",
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    dispatched_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    notes = models.TextField(
        blank=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_dispatch_batches",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Dispatch Batch #{self.id}"