from django.db import migrations


def backfill_customer_branch_memberships(apps, schema_editor):
    Customer = apps.get_model("freight", "Customer")
    Membership = apps.get_model(
        "freight",
        "CustomerBranchMembership",
    )

    for customer in Customer.objects.select_related("user").all():
        branch_id = customer.user.branch_id

        if not branch_id:
            continue

        Membership.objects.get_or_create(
            customer_id=customer.id,
            branch_id=branch_id,
            defaults={
                "status": "active",
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("freight", "0015_auto_20260926_0919"),
    ]

    operations = [
        migrations.RunPython(
            backfill_customer_branch_memberships,
            migrations.RunPython.noop,
        ),
    ]