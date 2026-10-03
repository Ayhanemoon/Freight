from django.conf import settings
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class CustomerRegistrationInvitation(models.Model):
    branch = models.ForeignKey(
        "freight.Branch",
        on_delete=models.PROTECT,
        related_name="customer_registration_invitations",
    )

    token_hash = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_customer_registration_invitations",
    )

    customer = models.ForeignKey(
        "freight.Customer",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="registration_invitations",
    )

    target_mobile = PhoneNumberField(
        null=True,
        blank=True,
    )

    expires_at = models.DateTimeField()

    max_uses = models.PositiveIntegerField(
        default=1,
    )

    used_count = models.PositiveIntegerField(
        default=0,
    )

    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(customer__isnull=True)
                | models.Q(target_mobile__isnull=True),
                name="invitation_target_not_both",
            ),
            models.CheckConstraint(
                check=models.Q(max_uses__gt=0),
                name="invitation_max_uses_positive",
            ),
            models.CheckConstraint(
                check=models.Q(used_count__lte=models.F("max_uses")),
                name="invitation_used_count_lte_max_uses",
            ),
        ]

    def __str__(self):
        return "{} - {}".format(
            self.branch,
            self.created_at,
        )