from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand


ROLES = [
    'SuperAdmin',
    'BranchManager',
    'Operator',
    'CargoCollector',
    'Dispatcher',
    'Customer',
]


class Command(BaseCommand):
    help = 'Create default user roles'

    def handle(self, *args, **options):
        for role in ROLES:
            group, created = Group.objects.get_or_create(name=role)

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created role: {role}')
                )
            else:
                self.stdout.write(f'Role already exists: {role}')

        self.stdout.write(self.style.SUCCESS('Role creation completed.'))