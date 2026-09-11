# models/dispatch_batch.py

from django.conf import settings
from django.db import models

from freight.models import Branch


class DispatchBatch(models.Model):

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        READY = "ready", "Ready"
        ASSIGNED = "assigned", "Assigned"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
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

    completed_at = models.DateTimeField(
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
        permissions = [
            ("assign_dispatcher", "Can assign dispatcher"),
            ("add_order_to_dispatch", "Can add order to dispatch"),
            ("remove_order_from_dispatch", "Can remove order from dispatch"),
            ("start_dispatch", "Can start dispatch"),
            ("complete_dispatch", "Can complete dispatch"),
        ]

    def __str__(self):
        return f"Dispatch Batch #{self.id}"