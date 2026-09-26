from django.conf import settings
from django.db import models


class CustomerBranchMembership(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"
        ENDED = "ended", "Ended"

    customer = models.ForeignKey(
        "freight.Customer",
        on_delete=models.CASCADE,
        related_name="branch_memberships",
    )

    branch = models.ForeignKey(
        "freight.Branch",
        on_delete=models.CASCADE,
        related_name="customer_memberships",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_customer_memberships",
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["customer", "branch"],
                name="unique_customer_branch_membership",
            )
        ]

    def __str__(self):
        return "{} - {}".format(
            self.customer,
            self.branch,
        )
    