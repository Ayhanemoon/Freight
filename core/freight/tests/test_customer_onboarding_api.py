from django.contrib.auth.models import Group
from rest_framework import status

from freight.constants import Roles
from freight.models import Customer
from freight.tests.base import FreightAPITestCase


class CustomerOnboardingAPITests(FreightAPITestCase):
    url = "/freight/api/v1/customers/onboarding/"

    def test_unauthenticated_user_cannot_onboard(self):
        self.unauthenticate()

        response = self.client.post(
            self.url,
            {
                "customer_type": "person",
                "first_name": "Ali",
                "last_name": "Ahmadi",
                "national_id": "0012345678",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_person_customer_can_onboard(self):
        user = self.create_user(
            mobile="09121111201",
        )
        self.authenticate(user)

        response = self.client.post(
            self.url,
            {
                "customer_type": "person",
                "first_name": "Ali",
                "last_name": "Ahmadi",
                "national_id": "0012345678",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        customer = Customer.objects.get(user=user)

        self.assertEqual(
            response.data["id"],
            customer.id,
        )
        self.assertEqual(
            response.data["customer_type"],
            Customer.CustomerType.PERSON,
        )
        self.assertEqual(
            response.data["first_name"],
            "Ali",
        )
        self.assertEqual(
            response.data["last_name"],
            "Ahmadi",
        )
        self.assertEqual(
            response.data["national_id"],
            "0012345678",
        )

        self.assertTrue(
            user.groups.filter(
                name=Roles.CUSTOMER,
            ).exists()
        )

    def test_company_customer_can_onboard(self):
        user = self.create_user(
            mobile="09121111202",
        )
        self.authenticate(user)

        response = self.client.post(
            self.url,
            {
                "customer_type": "company",
                "company_name": "Example Co",
                "company_registration_no": "123456",
                "economic_code": "987654321",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        customer = Customer.objects.get(user=user)

        self.assertEqual(
            response.data["id"],
            customer.id,
        )
        self.assertEqual(
            response.data["customer_type"],
            Customer.CustomerType.COMPANY,
        )
        self.assertEqual(
            response.data["company_name"],
            "Example Co",
        )

    def test_existing_customer_cannot_onboard_again(self):
        user = self.create_user(
            mobile="09121111203",
        )
        self.create_customer(user=user)

        self.authenticate(user)

        response = self.client.post(
            self.url,
            {
                "customer_type": "person",
                "first_name": "Ali",
                "last_name": "Ahmadi",
                "national_id": "0012345678",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_invalid_person_data_is_rejected(self):
        user = self.create_user(
            mobile="09121111204",
        )
        self.authenticate(user)

        response = self.client.post(
            self.url,
            {
                "customer_type": "person",
                "first_name": "Ali",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertFalse(
            Customer.objects.filter(user=user).exists()
        )

    def test_invalid_company_data_is_rejected(self):
        user = self.create_user(
            mobile="09121111205",
        )
        self.authenticate(user)

        response = self.client.post(
            self.url,
            {
                "customer_type": "company",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertFalse(
            Customer.objects.filter(user=user).exists()
        )

    def test_user_id_cannot_be_used_to_create_customer_for_another_user(self):
        user = self.create_user(
            mobile="09121111206",
        )
        other_user = self.create_user(
            mobile="09121111207",
        )

        self.authenticate(user)

        response = self.client.post(
            self.url,
            {
                "user_id": other_user.id,
                "customer_type": "person",
                "first_name": "Ali",
                "last_name": "Ahmadi",
                "national_id": "0012345678",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertTrue(
            Customer.objects.filter(user=user).exists()
        )

        self.assertFalse(
            Customer.objects.filter(user=other_user).exists()
        )

    def test_branch_id_is_not_used_during_normal_onboarding(self):
        user = self.create_user(
            mobile="09121111208",
        )
        branch = self.create_branch()

        self.authenticate(user)

        response = self.client.post(
            self.url,
            {
                "customer_type": "person",
                "first_name": "Ali",
                "last_name": "Ahmadi",
                "national_id": "0012345678",
                "branch_id": branch.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        customer = Customer.objects.get(user=user)

        self.assertFalse(
            customer.branch_memberships.exists()
        )