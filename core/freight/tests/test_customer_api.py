from django.contrib.auth.models import Group
from rest_framework import status

from freight.constants import Roles
from freight.models import CustomerBranchMembership
from freight.tests.base import FreightAPITestCase


class CustomerAPIAccessTests(FreightAPITestCase):
    url = "/freight/api/v1/customers/"

    def add_role(self, user, role):
        group, _ = Group.objects.get_or_create(name=role)
        user.groups.add(group)

    def test_unauthenticated_user_cannot_access_customers(self):
        self.unauthenticate()

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_superuser_can_see_all_customers(self):
        user_one = self.create_user(mobile="09120000001")
        user_two = self.create_user(mobile="09120000002")

        self.create_customer(user=user_one)
        self.create_customer(user=user_two)

        admin = self.create_user(
            mobile="09120000003",
            is_superuser=True,
            is_staff=True,
        )

        self.authenticate(admin)

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(response.data["count"], 2)

    def test_customer_can_see_only_own_profile(self):
        own_user = self.create_user(mobile="09120000004")
        other_user = self.create_user(mobile="09120000005")

        own_customer = self.create_customer(user=own_user)
        self.create_customer(user=other_user)

        self.add_role(own_user, Roles.CUSTOMER)
        self.authenticate(own_user)

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["id"],
            own_customer.id,
        )

    def test_customer_cannot_retrieve_another_customer(self):
        own_user = self.create_user(mobile="09120000006")
        other_user = self.create_user(mobile="09120000007")

        self.create_customer(user=own_user)
        other_customer = self.create_customer(user=other_user)

        self.add_role(own_user, Roles.CUSTOMER)
        self.authenticate(own_user)

        response = self.client.get(
            "{}{}/".format(self.url, other_customer.id),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_branch_manager_sees_only_active_customers_in_own_branch(self):
        own_branch = self.create_branch(
            name="Tehran Branch",
            code="THR",
        )
        other_branch = self.create_branch(
            name="Mashhad Branch",
            code="MHD",
            city="Mashhad",
        )

        manager = self.create_user(
            mobile="09120000008",
            branch=own_branch,
        )
        self.add_role(manager, Roles.BRANCH_MANAGER)

        active_user = self.create_user(mobile="09120000009")
        active_customer = self.create_customer(user=active_user)

        other_user = self.create_user(mobile="09120000010")
        other_customer = self.create_customer(user=other_user)

        suspended_user = self.create_user(mobile="09120000011")
        suspended_customer = self.create_customer(user=suspended_user)

        CustomerBranchMembership.objects.create(
            customer=active_customer,
            branch=own_branch,
            status=CustomerBranchMembership.Status.ACTIVE,
        )

        CustomerBranchMembership.objects.create(
            customer=other_customer,
            branch=other_branch,
            status=CustomerBranchMembership.Status.ACTIVE,
        )

        CustomerBranchMembership.objects.create(
            customer=suspended_customer,
            branch=own_branch,
            status=CustomerBranchMembership.Status.SUSPENDED,
        )

        self.authenticate(manager)

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["id"],
            active_customer.id,
        )

    def test_branch_manager_without_branch_sees_no_customers(self):
        manager = self.create_user(
            mobile="09120000012",
        )
        self.add_role(manager, Roles.BRANCH_MANAGER)

        customer_user = self.create_user(
            mobile="09120000013",
        )
        self.create_customer(user=customer_user)

        self.authenticate(manager)

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(response.data["count"], 0)

    def test_operational_roles_cannot_access_customers(self):
        roles = [
            Roles.OPERATOR,
            Roles.DISPATCHER,
            Roles.CARGO_COLLECTOR,
        ]

        for index, role in enumerate(roles, start=14):
            user = self.create_user(
                mobile="091200000{}".format(index),
            )
            self.add_role(user, role)
            self.authenticate(user)

            response = self.client.get(self.url)

            self.assertEqual(
                response.status_code,
                status.HTTP_403_FORBIDDEN,
                msg=role,
            )

    def test_customer_mutations_are_currently_denied(self):
        user = self.create_user(
            mobile="09120000017",
        )
        customer = self.create_customer(user=user)

        self.add_role(user, Roles.CUSTOMER)
        self.authenticate(user)

        create_response = self.client.post(
            self.url,
            {},
        )

        self.assertEqual(
            create_response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        update_response = self.client.patch(
            "{}{}/".format(self.url, customer.id),
            {"first_name": "Changed"},
            format="json",
        )

        self.assertEqual(
            update_response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        delete_response = self.client.delete(
            "{}{}/".format(self.url, customer.id),
        )

        self.assertEqual(
            delete_response.status_code,
            status.HTTP_403_FORBIDDEN,
        )