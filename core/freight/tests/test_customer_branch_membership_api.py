from django.urls import reverse
from rest_framework import status

from freight.models import CustomerBranchMembership
from freight.tests.base import FreightAPITestCase


class CustomerBranchMembershipRequestAPITests(
    FreightAPITestCase
):

    def setUp(self):
        self.customer_user = self.create_user(
            mobile="09122222201",
        )

        self.customer = self.create_customer(
            user=self.customer_user,
        )

        self.tehran = self.create_branch(
            name="Tehran Branch",
            code="THR",
        )

        self.mashhad = self.create_branch(
            name="Mashhad Branch",
            code="MHD",
            city="Mashhad",
        )

        self.url = reverse(
            "freight:freight-api-v1:customer-branch-membership-request"
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_customer_can_request_branch_membership(self):
        self.authenticate(self.customer_user)

        response = self.client.post(
            self.url,
            {
                "branch": self.tehran.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["branch"]["id"],
            self.tehran.id,
        )

        self.assertEqual(
            response.data["branch"]["name"],
            self.tehran.name,
        )

        self.assertEqual(
            response.data["status"],
            CustomerBranchMembership.Status.PENDING,
        )

        self.assertEqual(
            CustomerBranchMembership.objects.filter(
                customer=self.customer,
                branch=self.tehran,
            ).count(),
            1,
        )

    def test_unauthenticated_user_cannot_request_membership(self):
        response = self.client.post(
            self.url,
            {
                "branch": self.tehran.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_user_without_customer_profile_cannot_request_membership(
        self,
    ):
        user = self.create_user(
            mobile="09122222202",
        )

        self.authenticate(user)

        response = self.client.post(
            self.url,
            {
                "branch": self.tehran.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertFalse(
            CustomerBranchMembership.objects.exists()
        )

    def test_inactive_branch_cannot_be_requested(self):
        self.tehran.is_active = False
        self.tehran.save(
            update_fields=["is_active"]
        )

        self.authenticate(self.customer_user)

        response = self.client.post(
            self.url,
            {
                "branch": self.tehran.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertFalse(
            CustomerBranchMembership.objects.filter(
                customer=self.customer,
                branch=self.tehran,
            ).exists()
        )

    def test_customer_cannot_request_same_branch_twice(self):
        self.authenticate(self.customer_user)

        first_response = self.client.post(
            self.url,
            {
                "branch": self.tehran.id,
            },
            format="json",
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_201_CREATED,
        )

        second_response = self.client.post(
            self.url,
            {
                "branch": self.tehran.id,
            },
            format="json",
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            CustomerBranchMembership.objects.filter(
                customer=self.customer,
                branch=self.tehran,
            ).count(),
            1,
        )

    def test_customer_can_request_multiple_branches(self):
        self.authenticate(self.customer_user)

        first_response = self.client.post(
            self.url,
            {
                "branch": self.tehran.id,
            },
            format="json",
        )

        second_response = self.client.post(
            self.url,
            {
                "branch": self.mashhad.id,
            },
            format="json",
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            CustomerBranchMembership.objects.filter(
                customer=self.customer,
            ).count(),
            2,
        )

    def test_client_cannot_choose_customer(self):
        other_user = self.create_user(
            mobile="09122222203",
        )

        other_customer = self.create_customer(
            user=other_user,
        )

        self.authenticate(self.customer_user)

        response = self.client.post(
            self.url,
            {
                "branch": self.tehran.id,
                "customer": other_customer.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        membership = CustomerBranchMembership.objects.get(
            customer=self.customer,
            branch=self.tehran,
        )

        self.assertEqual(
            membership.customer_id,
            self.customer.id,
        )

        self.assertNotEqual(
            membership.customer_id,
            other_customer.id,
        )

    def test_client_cannot_create_active_membership(self):
        self.authenticate(self.customer_user)

        response = self.client.post(
            self.url,
            {
                "branch": self.tehran.id,
                "status": CustomerBranchMembership.Status.ACTIVE,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        membership = CustomerBranchMembership.objects.get(
            customer=self.customer,
            branch=self.tehran,
        )

        self.assertEqual(
            membership.status,
            CustomerBranchMembership.Status.PENDING,
        )

    def test_invalid_branch_id_is_rejected(self):
        self.authenticate(self.customer_user)

        response = self.client.post(
            self.url,
            {
                "branch": 999999,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertFalse(
            CustomerBranchMembership.objects.filter(
                customer=self.customer,
            ).exists()
        )

    def test_branch_is_required(self):
        self.authenticate(self.customer_user)

        response = self.client.post(
            self.url,
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )