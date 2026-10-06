from django.urls import reverse

from freight.constants import Roles
from freight.models import CustomerBranchMembership

from .base import FreightAPITestCase


class ShipmentOrderAPITests(FreightAPITestCase):

    def setUp(self):
        self.branch = self.create_branch(
            name="Tehran Branch",
            code="THR",
        )

        self.other_branch = self.create_branch(
            name="Karaj Branch",
            code="KRJ",
            city="Karaj",
        )

        self.branch_manager = self.create_user(
            mobile="09121111111",
            branch=self.branch,
            is_staff=True,
        )
        self.branch_manager.groups.create(
            name=Roles.BRANCH_MANAGER,
        )

        self.operator = self.create_user(
            mobile="09121111112",
            branch=self.branch,
            is_staff=True,
        )
        self.operator.groups.create(
            name=Roles.OPERATOR,
        )

        self.customer_user = self.create_user(
            mobile="09121111113",
        )
        self.customer = self.create_customer(
            user=self.customer_user,
        )

        self.other_customer_user = self.create_user(
            mobile="09121111114",
        )
        self.other_customer = self.create_customer(
            user=self.other_customer_user,
        )

        self.url = reverse(
            "freight:freight-api-v1:shipment-order-list"
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def create_active_membership(self, customer, branch):
        return CustomerBranchMembership.objects.create(
            customer=customer,
            branch=branch,
            status=CustomerBranchMembership.Status.ACTIVE,
        )

    def create_membership(
        self,
        customer,
        branch,
        status,
    ):
        return CustomerBranchMembership.objects.create(
            customer=customer,
            branch=branch,
            status=status,
        )

    def valid_order_payload(self, branch):
        return {
            "branch": branch.id,
            "preferred_freight_company": None,
            "sender_name": "Sender",
            "sender_mobile": "09125555555",
            "sender_address": "Sender address",
            "receiver_name": "Receiver",
            "receiver_mobile": "09126666666",
            "receiver_address": "Receiver address",
            "shipment_description": "Test shipment",
        }

    # ------------------------------------------------------------------
    # Customer - Create
    # ------------------------------------------------------------------

    def test_customer_can_create_order_for_active_membership(self):
        self.create_active_membership(
            self.customer,
            self.branch,
        )

        self.authenticate(self.customer_user)

        response = self.client.post(
            self.url,
            self.valid_order_payload(self.branch),
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        self.assertEqual(
            response.data["branch"],
            self.branch.id,
        )

        self.assertEqual(
            response.data["customer"],
            self.customer.id,
        )

        self.assertEqual(
            response.data["created_by"],
            self.customer_user.id,
        )

    def test_customer_can_choose_any_active_membership_branch(self):
        self.create_active_membership(
            self.customer,
            self.branch,
        )

        self.create_active_membership(
            self.customer,
            self.other_branch,
        )

        self.authenticate(self.customer_user)

        response = self.client.post(
            self.url,
            self.valid_order_payload(self.other_branch),
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        self.assertEqual(
            response.data["branch"],
            self.other_branch.id,
        )

        self.assertEqual(
            response.data["customer"],
            self.customer.id,
        )

    def test_customer_cannot_create_order_without_active_membership(self):
        self.authenticate(self.customer_user)

        response = self.client.post(
            self.url,
            self.valid_order_payload(self.branch),
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_customer_cannot_create_order_for_pending_membership(self):
        self.create_membership(
            self.customer,
            self.branch,
            CustomerBranchMembership.Status.PENDING,
        )

        self.authenticate(self.customer_user)

        response = self.client.post(
            self.url,
            self.valid_order_payload(self.branch),
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_customer_cannot_create_order_for_suspended_membership(self):
        self.create_membership(
            self.customer,
            self.branch,
            CustomerBranchMembership.Status.SUSPENDED,
        )

        self.authenticate(self.customer_user)

        response = self.client.post(
            self.url,
            self.valid_order_payload(self.branch),
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_customer_cannot_create_order_for_ended_membership(self):
        self.create_membership(
            self.customer,
            self.branch,
            CustomerBranchMembership.Status.ENDED,
        )

        self.authenticate(self.customer_user)

        response = self.client.post(
            self.url,
            self.valid_order_payload(self.branch),
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    # ------------------------------------------------------------------
    # Customer - List / Retrieve
    # ------------------------------------------------------------------

    def test_customer_can_only_list_own_orders(self):
        own_order = self.create_order(
            branch=self.branch,
            customer=self.customer,
            created_by=self.customer_user,
        )

        self.create_order(
            branch=self.branch,
            customer=self.other_customer,
            created_by=self.other_customer_user,
        )

        self.authenticate(self.customer_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        returned_ids = {
            item["id"]
            for item in response.data["results"]
        }

        self.assertEqual(
            returned_ids,
            {own_order.id},
        )

    def test_customer_cannot_retrieve_other_customer_order(self):
        other_order = self.create_order(
            branch=self.branch,
            customer=self.other_customer,
            created_by=self.other_customer_user,
        )

        self.authenticate(self.customer_user)

        response = self.client.get(
            reverse(
                "freight:freight-api-v1:shipment-order-detail",
                kwargs={"pk": other_order.pk},
            )
        )

        self.assertEqual(response.status_code, 404)

    # ------------------------------------------------------------------
    # Customer - Update
    # ------------------------------------------------------------------

    def test_customer_can_update_own_draft_order(self):
        order = self.create_order(
            branch=self.branch,
            customer=self.customer,
            created_by=self.customer_user,
            status="draft",
        )

        self.authenticate(self.customer_user)

        response = self.client.patch(
            reverse(
                "freight:freight-api-v1:shipment-order-detail",
                kwargs={"pk": order.pk},
            ),
            {
                "sender_name": "Updated Sender",
                "shipment_description": "Updated shipment",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        order.refresh_from_db()

        self.assertEqual(
            order.sender_name,
            "Updated Sender",
        )

        self.assertEqual(
            order.shipment_description,
            "Updated shipment",
        )

    def test_customer_cannot_update_own_non_draft_order(self):
        order = self.create_order(
            branch=self.branch,
            customer=self.customer,
            created_by=self.customer_user,
        )

        self.authenticate(self.customer_user)

        response = self.client.patch(
            reverse(
                "freight:freight-api-v1:shipment-order-detail",
                kwargs={"pk": order.pk},
            ),
            {
                "sender_name": "Updated Sender",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    # ------------------------------------------------------------------
    # BranchManager - Create
    # ------------------------------------------------------------------

    def test_branch_manager_can_create_order_in_own_branch(self):
        self.authenticate(self.branch_manager)

        response = self.client.post(
            self.url,
            self.valid_order_payload(self.branch),
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        self.assertEqual(
            response.data["branch"],
            self.branch.id,
        )

        self.assertEqual(
            response.data["created_by"],
            self.branch_manager.id,
        )

    def test_branch_manager_cannot_create_order_in_other_branch(self):
        self.authenticate(self.branch_manager)

        response = self.client.post(
            self.url,
            self.valid_order_payload(self.other_branch),
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    # ------------------------------------------------------------------
    # Operator - Authorization
    # ------------------------------------------------------------------

    def test_operator_cannot_create_order(self):
        self.authenticate(self.operator)

        response = self.client.post(
            self.url,
            self.valid_order_payload(self.branch),
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_operator_can_access_orders_in_own_branch(self):
        order = self.create_order(
            branch=self.branch,
            customer=self.customer,
            created_by=self.customer_user,
        )

        self.authenticate(self.operator)

        response = self.client.get(
            self.url,
        )

        self.assertEqual(response.status_code, 200)

        returned_ids = {
            item["id"]
            for item in response.data["results"]
        }

        self.assertEqual(
            returned_ids,
            {order.id},
        )

    def test_operator_cannot_access_orders_in_other_branch(self):
        other_order = self.create_order(
            branch=self.other_branch,
            customer=self.customer,
            created_by=self.customer_user,
        )

        self.authenticate(self.operator)

        response = self.client.get(
            reverse(
                "freight:freight-api-v1:shipment-order-detail",
                kwargs={"pk": other_order.pk},
            )
        )

        self.assertEqual(response.status_code, 404)

    # ------------------------------------------------------------------
    # Update authorization
    # ------------------------------------------------------------------

    def test_operator_cannot_update_shipment_order(self):
        order = self.create_order(
            branch=self.branch,
            customer=self.customer,
            created_by=self.customer_user,
        )

        self.authenticate(self.operator)

        response = self.client.patch(
            reverse(
                "freight:freight-api-v1:shipment-order-detail",
                kwargs={"pk": order.pk},
            ),
            {
                "sender_name": "Updated Sender",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_branch_manager_can_update_order_in_own_branch(self):
        order = self.create_order(
            branch=self.branch,
            customer=self.customer,
            created_by=self.customer_user,
        )

        self.authenticate(self.branch_manager)

        response = self.client.patch(
            reverse(
                "freight:freight-api-v1:shipment-order-detail",
                kwargs={"pk": order.pk},
            ),
            {
                "sender_name": "Updated Sender",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        order.refresh_from_db()

        self.assertEqual(
            order.sender_name,
            "Updated Sender",
        )

    def test_branch_manager_cannot_update_order_in_other_branch(self):
        order = self.create_order(
            branch=self.other_branch,
            customer=self.customer,
            created_by=self.customer_user,
        )

        self.authenticate(self.branch_manager)

        response = self.client.patch(
            reverse(
                "freight:freight-api-v1:shipment-order-detail",
                kwargs={"pk": order.pk},
            ),
            {
                "sender_name": "Updated Sender",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 404)

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def test_shipment_order_cannot_be_deleted(self):
        order = self.create_order(
            branch=self.branch,
            customer=self.customer,
            created_by=self.customer_user,
        )

        self.authenticate(self.branch_manager)

        response = self.client.delete(
            reverse(
                "freight:freight-api-v1:shipment-order-detail",
                kwargs={"pk": order.pk},
            )
        )

        self.assertEqual(response.status_code, 403)

        self.assertTrue(
            type(order).objects.filter(pk=order.pk).exists()
        )

    # ------------------------------------------------------------------
    # Unauthenticated
    # ------------------------------------------------------------------

    def test_unauthenticated_user_cannot_access_orders(self):
        self.unauthenticate()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)