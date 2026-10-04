from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from freight.constants import Roles
from rest_framework.exceptions import PermissionDenied, ValidationError

from freight.models import Customer, CustomerBranchMembership
from freight.services.customer_onboarding import onboard_customer
from freight.tests.base import FreightAPITestCase


class CustomerOnboardingServiceTests(FreightAPITestCase):

    def test_person_customer_can_be_onboarded(self):
        user = self.create_user(
            mobile="09121111111",
        )

        customer, membership = onboard_customer(
            user=user,
            customer_type=Customer.CustomerType.PERSON,
            first_name="Ali",
            last_name="Ahmadi",
            national_id="0012345678",
        )

        self.assertEqual(customer.user_id, user.id)
        self.assertEqual(
            customer.customer_type,
            Customer.CustomerType.PERSON,
        )
        self.assertEqual(customer.first_name, "Ali")
        self.assertEqual(customer.last_name, "Ahmadi")
        self.assertEqual(customer.national_id, "0012345678")
        self.assertIsNone(membership)

    def test_company_customer_can_be_onboarded(self):
        user = self.create_user(
            mobile="09121111112",
        )

        customer, membership = onboard_customer(
            user=user,
            customer_type=Customer.CustomerType.COMPANY,
            company_name="Example Co",
            company_registration_no="123456",
            economic_code="987654321",
        )

        self.assertEqual(customer.user_id, user.id)
        self.assertEqual(
            customer.customer_type,
            Customer.CustomerType.COMPANY,
        )
        self.assertEqual(
            customer.company_name,
            "Example Co",
        )
        self.assertEqual(
            customer.company_registration_no,
            "123456",
        )
        self.assertEqual(
            customer.economic_code,
            "987654321",
        )
        self.assertIsNone(membership)

    def test_person_requires_first_and_last_name(self):
        user = self.create_user(
            mobile="09121111113",
        )

        with self.assertRaises(ValidationError):
            onboard_customer(
                user=user,
                customer_type=Customer.CustomerType.PERSON,
                national_id="0012345678",
            )

    def test_person_requires_national_id(self):
        user = self.create_user(
            mobile="09121111114",
        )

        with self.assertRaises(ValidationError):
            onboard_customer(
                user=user,
                customer_type=Customer.CustomerType.PERSON,
                first_name="Ali",
                last_name="Ahmadi",
            )

    def test_company_requires_company_name(self):
        user = self.create_user(
            mobile="09121111115",
        )

        with self.assertRaises(ValidationError):
            onboard_customer(
                user=user,
                customer_type=Customer.CustomerType.COMPANY,
            )

    def test_person_cannot_send_company_fields(self):
        user = self.create_user(
            mobile="09121111116",
        )

        with self.assertRaises(ValidationError):
            onboard_customer(
                user=user,
                customer_type=Customer.CustomerType.PERSON,
                first_name="Ali",
                last_name="Ahmadi",
                national_id="0012345678",
                company_name="Example Co",
            )

    def test_company_cannot_send_person_fields(self):
        user = self.create_user(
            mobile="09121111117",
        )

        with self.assertRaises(ValidationError):
            onboard_customer(
                user=user,
                customer_type=Customer.CustomerType.COMPANY,
                company_name="Example Co",
                first_name="Ali",
            )

    def test_existing_customer_cannot_onboard_again(self):
        user = self.create_user(
            mobile="09121111118",
        )

        self.create_customer(
            user=user,
        )

        with self.assertRaises(ValidationError):
            onboard_customer(
                user=user,
                customer_type=Customer.CustomerType.PERSON,
                first_name="Ali",
                last_name="Ahmadi",
                national_id="0012345678",
            )

    def test_inactive_user_cannot_onboard(self):
        user = self.create_user(
            mobile="09121111119",
            is_active=False,
        )

        with self.assertRaises(PermissionDenied):
            onboard_customer(
                user=user,
                customer_type=Customer.CustomerType.PERSON,
                first_name="Ali",
                last_name="Ahmadi",
                national_id="0012345678",
            )

    def test_branch_membership_is_created_as_pending(self):
        user = self.create_user(
            mobile="09121111120",
        )

        branch = self.create_branch()

        customer, membership = onboard_customer(
            user=user,
            customer_type=Customer.CustomerType.PERSON,
            first_name="Ali",
            last_name="Ahmadi",
            national_id="0012345678",
            branch=branch,
        )

        self.assertIsNotNone(membership)
        self.assertEqual(
            membership.customer_id,
            customer.id,
        )
        self.assertEqual(
            membership.branch_id,
            branch.id,
        )
        self.assertEqual(
            membership.status,
            CustomerBranchMembership.Status.PENDING,
        )
        self.assertIsNone(membership.approved_at)
        self.assertIsNone(membership.approved_by)

    def test_inactive_branch_cannot_be_requested(self):
        user = self.create_user(
            mobile="09121111121",
        )

        branch = self.create_branch(
            is_active=False,
        )

        with self.assertRaises(ValidationError):
            onboard_customer(
                user=user,
                customer_type=Customer.CustomerType.PERSON,
                first_name="Ali",
                last_name="Ahmadi",
                national_id="0012345678",
                branch=branch,
            )

        self.assertFalse(
            Customer.objects.filter(user=user).exists()
        )

    def test_unauthenticated_user_cannot_onboard(self):
        user = AnonymousUser()

        with self.assertRaises(PermissionDenied):
            onboard_customer(
                user=user,
                customer_type=Customer.CustomerType.PERSON,
                first_name="Ali",
                last_name="Ahmadi",
                national_id="0012345678",
            )

    def test_invalid_customer_type_is_rejected(self):
        user = self.create_user(
            mobile="09121111122",
        )

        with self.assertRaises(ValidationError):
            onboard_customer(
                user=user,
                customer_type="invalid",
                first_name="Ali",
                last_name="Ahmadi",
                national_id="0012345678",
            )

        self.assertFalse(
            Customer.objects.filter(user=user).exists()
        )

    def test_onboarding_rolls_back_customer_and_role_when_membership_creation_fails(
        self,
    ):
        user = self.create_user(
            mobile="09121111123",
        )
        branch = self.create_branch(
            code="ROLLBACK",
        )

        with patch(
            "freight.services.customer_onboarding."
            "CustomerBranchMembership.objects.create",
            side_effect=RuntimeError("membership creation failed"),
        ):
            with self.assertRaises(RuntimeError):
                onboard_customer(
                    user=user,
                    customer_type=Customer.CustomerType.PERSON,
                    first_name="Ali",
                    last_name="Ahmadi",
                    national_id="0012345678",
                    branch=branch,
                )

        self.assertFalse(
            Customer.objects.filter(user=user).exists()
        )

        self.assertFalse(
            user.groups.filter(
                name=Roles.CUSTOMER,
            ).exists()
        )

    def test_onboarding_assigns_customer_role(self):
        user = self.create_user(
            mobile="09121111124",
        )

        customer, membership = onboard_customer(
            user=user,
            customer_type=Customer.CustomerType.PERSON,
            first_name="Ali",
            last_name="Ahmadi",
            national_id="0012345678",
        )

        self.assertIsNotNone(customer)

        self.assertTrue(
            user.groups.filter(
                name=Roles.CUSTOMER,
            ).exists()
        )