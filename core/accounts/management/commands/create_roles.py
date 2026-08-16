from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


ROLE_PERMISSIONS = {
    "SuperAdmin": [
        "*",
    ],
    "BranchManager": [
        "assign_collection_task",
        "cancel_collection_task",
    ],
    "Operator": [
        "assign_collection_task",
        "cancel_collection_task",
    ],
    "CargoCollector": [
        "start_collection_task",
        "verify_collection_task",
        "complete_collection_task",
    ],
    "Dispatcher": [],
    "Customer": [],
}


class Command(BaseCommand):
    help = "Create default user roles and assign permissions"

    def handle(self, *args, **options):

        for role_name, permission_codenames in ROLE_PERMISSIONS.items():

            group, created = Group.objects.get_or_create(
                name=role_name
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created role: {role_name}"
                    )
                )
            else:
                self.stdout.write(
                    f"Role already exists: {role_name}"
                )

            # SuperAdmin is handled separately.
            if permission_codenames == ["*"]:
                continue

            permissions = Permission.objects.filter(
                codename__in=permission_codenames
            )

            group.permissions.set(permissions)

            self.stdout.write(
                f"Assigned {permissions.count()} permissions "
                f"to {role_name}"
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Role and permission setup completed."
            )
        )