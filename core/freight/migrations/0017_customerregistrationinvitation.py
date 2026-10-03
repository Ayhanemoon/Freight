from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("freight", "0016_backfill_customer_branch_memberships"),
    ]

    operations = [
        migrations.CreateModel(
            name="CustomerRegistrationInvitation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "token_hash",
                    models.CharField(
                        db_index=True,
                        max_length=64,
                        unique=True,
                    ),
                ),
                (
                    "target_mobile",
                    phonenumber_field.modelfields.PhoneNumberField(
                        blank=True,
                        null=True,
                    ),
                ),
                (
                    "expires_at",
                    models.DateTimeField(),
                ),
                (
                    "max_uses",
                    models.PositiveIntegerField(default=1),
                ),
                (
                    "used_count",
                    models.PositiveIntegerField(default=0),
                ),
                (
                    "revoked_at",
                    models.DateTimeField(
                        blank=True,
                        null=True,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "branch",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="customer_registration_invitations",
                        to="freight.branch",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="created_customer_registration_invitations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "customer",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="registration_invitations",
                        to="freight.customer",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="customerregistrationinvitation",
            constraint=models.CheckConstraint(
                check=models.Q(customer__isnull=True)
                | models.Q(target_mobile__isnull=True),
                name="invitation_target_not_both",
            ),
        ),
        migrations.AddConstraint(
            model_name="customerregistrationinvitation",
            constraint=models.CheckConstraint(
                check=models.Q(max_uses__gt=0),
                name="invitation_max_uses_positive",
            ),
        ),
        migrations.AddConstraint(
            model_name="customerregistrationinvitation",
            constraint=models.CheckConstraint(
                check=models.Q(
                    used_count__lte=models.F("max_uses")
                ),
                name="invitation_used_count_lte_max_uses",
            ),
        ),
    ]