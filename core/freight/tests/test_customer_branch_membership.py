from django.db import IntegrityError

from freight.models import CustomerBranchMembership
from freight.tests.base import FreightAPITestCase


class CustomerBranchMembershipModelTests(FreightAPITestCase):

    def test_customer_can_have_multiple_active_branch_memberships(self):
        customer_user = self.create_user(
            mobile="09120000001",
        )

        customer = self.create_customer(
            user=customer_user,
        )

        tehran = self.create_branch(
            name="Tehran Branch",
            code="THR",
        )

        mashhad = self.create_branch(
            name="Mashhad Branch",
            code="MHD",
            city="Mashhad",
        )

        first = CustomerBranchMembership.objects.create(
            customer=customer,
            branch=tehran,
            status=CustomerBranchMembership.Status.ACTIVE,
        )

        second = CustomerBranchMembership.objects.create(
            customer=customer,
            branch=mashhad,
            status=CustomerBranchMembership.Status.ACTIVE,
        )

        self.assertEqual(
            customer.branch_memberships.count(),
            2,
        )

        self.assertEqual(
            first.status,
            CustomerBranchMembership.Status.ACTIVE,
        )

        self.assertEqual(
            second.status,
            CustomerBranchMembership.Status.ACTIVE,
        )

    def test_customer_cannot_have_duplicate_membership_for_same_branch(self):
        customer_user = self.create_user(
            mobile="09120000002",
        )

        customer = self.create_customer(
            user=customer_user,
        )

        branch = self.create_branch()

        CustomerBranchMembership.objects.create(
            customer=customer,
            branch=branch,
            status=CustomerBranchMembership.Status.ACTIVE,
        )

        with self.assertRaises(IntegrityError):
            CustomerBranchMembership.objects.create(
                customer=customer,
                branch=branch,
                status=CustomerBranchMembership.Status.ACTIVE,
            )