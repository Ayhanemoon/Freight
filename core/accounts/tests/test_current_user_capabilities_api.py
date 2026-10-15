
import pytest

from django.contrib.auth.models import Group, Permission
from django.urls import reverse
from rest_framework.test import APITestCase

from accounts.models import User
from freight.constants import Roles
from freight.models import Branch


@pytest.mark.django_db
class CurrentUserCapabilitiesAPITests(APITestCase):
    def setUp(self):
        self.branch = Branch.objects.create(
            name="Tehran Center",
            code="THR",
            city="Tehran",
        )

        self.user = User.objects.create_user(
            mobile="09121112222",
            password="testpass123",
            is_mobile_verified=True,
            branch=self.branch,
        )

        self.url = reverse(
            "accounts:api-v1:current-user-capabilities"
        )

    def test_capabilities_requires_authentication(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)

    def test_returns_user_roles_branch_and_permissions(self):
        manager_group = Group.objects.create(
            name=Roles.BRANCH_MANAGER,
        )
        self.user.groups.add(manager_group)

        permission = Permission.objects.get(
            codename="view_user",
            content_type__app_label="accounts",
        )
        self.user.user_permissions.add(permission)

        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user"]["id"], self.user.id)
        self.assertEqual(
            response.data["user"]["mobile"],
            str(self.user.mobile),
        )
        self.assertEqual(
            response.data["roles"],
            [Roles.BRANCH_MANAGER],
        )
        self.assertEqual(
            response.data["branch"],
            {
                "id": self.branch.id,
                "name": self.branch.name,
            },
        )
        self.assertIn(
            "accounts.view_user",
            response.data["permissions"],
        )

    def test_superuser_receives_super_admin_role(self):
        superuser = User.objects.create_superuser(
            mobile="09123334444",
            password="testpass123",
            branch=self.branch,
        )

        self.client.force_authenticate(user=superuser)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            Roles.SUPER_ADMIN,
            response.data["roles"],
        )