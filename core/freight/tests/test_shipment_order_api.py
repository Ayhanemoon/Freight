from django.urls import reverse
from django.contrib.auth.models import Group

from freight.constants import Roles
from freight.models import CustomerBranchMembership, ShipmentStatusHistory, ShipmentOrder

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
        customer_group, _ = Group.objects.get_or_create(
            name=Roles.CUSTOMER,
        )

        self.customer_user.groups.add(customer_group)
        self.customer = self.create_customer(
            user=self.customer_user,
        )

        self.other_customer_user = self.create_user(
            mobile="09121111114",
        )
        self.other_customer_user.groups.add(customer_group)
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

    def valid_staff_order_payload(self, branch, customer):
        payload = self.valid_order_payload(branch)
        payload["customer"] = customer.id
        return payload

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
            response.data["branch"]["id"],
            self.branch.id,
        )

        self.assertEqual(
            response.data["customer"]["id"],
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
            response.data["branch"]["id"],
            self.other_branch.id,
        )

        self.assertEqual(
            response.data["customer"]["id"],
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
        self.create_active_membership(
            self.customer,
            self.branch,
        )

        self.authenticate(self.branch_manager)

        response = self.client.post(
            self.url,
            self.valid_staff_order_payload(
                self.branch,
                self.customer,
            ),
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        self.assertEqual(
            response.data["branch"]["id"],
            self.branch.id,
        )

        self.assertEqual(
            response.data["customer"]["id"],
            self.customer.id,
        )

        self.assertEqual(
            response.data["created_by"],
            self.branch_manager.id,
        )

    def test_branch_manager_cannot_create_order_in_other_branch(self):
        self.create_active_membership(
            self.customer,
            self.other_branch,
        )

        self.authenticate(self.branch_manager)

        response = self.client.post(
            self.url,
            self.valid_staff_order_payload(
                self.other_branch,
                self.customer,
            ),
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_branch_manager_cannot_create_order_for_customer_of_other_branch(
        self,
    ):
        self.create_active_membership(
            self.other_customer,
            self.other_branch,
        )

        self.authenticate(self.branch_manager)

        response = self.client.post(
            self.url,
            self.valid_staff_order_payload(
                self.branch,
                self.other_customer,
            ),
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


    
    # ------------------------------------------------------------------
    # Customer - Submit
    # ------------------------------------------------------------------

    def test_customer_can_submit_own_draft_order(self):
        order = self.create_order(
            branch=self.branch,
            customer=self.customer,
            created_by=self.customer_user,
            status=ShipmentOrder.Status.DRAFT,
        )

        self.authenticate(self.customer_user)

        response = self.client.post(
            reverse(
                "freight:freight-api-v1:shipment-order-submit",
                kwargs={"pk": order.pk},
            ),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        order.refresh_from_db()

        self.assertEqual(
            order.status,
            ShipmentOrder.Status.SUBMITTED,
        )
        self.assertIsNotNone(order.submitted_at)

        self.assertEqual(
            response.data["status"],
            ShipmentOrder.Status.SUBMITTED,
        )
        self.assertIsNotNone(response.data["submitted_at"])

        self.assertTrue(
            ShipmentStatusHistory.objects.filter(
                shipment=order,
                from_status=ShipmentOrder.Status.DRAFT,
                to_status=ShipmentOrder.Status.SUBMITTED,
                changed_by=self.customer_user,
            ).exists()
        )

    def test_customer_cannot_submit_another_customers_order(self):
        order = self.create_order(
            branch=self.branch,
            customer=self.other_customer,
            created_by=self.other_customer_user,
            status=ShipmentOrder.Status.DRAFT,
        )

        self.authenticate(self.customer_user)

        response = self.client.post(
            reverse(
                "freight:freight-api-v1:shipment-order-submit",
                kwargs={"pk": order.pk},
            ),
            {},
            format="json",
        )

        # The queryset scopes customers to their own orders.
        self.assertEqual(response.status_code, 404)

        order.refresh_from_db()
        self.assertEqual(order.status, ShipmentOrder.Status.DRAFT)
        self.assertIsNone(order.submitted_at)

    def test_customer_cannot_submit_non_draft_order(self):
        order = self.create_order(
            branch=self.branch,
            customer=self.customer,
            created_by=self.customer_user,
            status=ShipmentOrder.Status.SUBMITTED,
        )

        self.authenticate(self.customer_user)

        response = self.client.post(
            reverse(
                "freight:freight-api-v1:shipment-order-submit",
                kwargs={"pk": order.pk},
            ),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_branch_manager_cannot_submit_customer_order(self):
        order = self.create_order(
            branch=self.branch,
            customer=self.customer,
            created_by=self.customer_user,
            status=ShipmentOrder.Status.DRAFT,
        )

        self.authenticate(self.branch_manager)

        response = self.client.post(
            reverse(
                "freight:freight-api-v1:shipment-order-submit",
                kwargs={"pk": order.pk},
            ),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

        order.refresh_from_db()
        self.assertEqual(order.status, ShipmentOrder.Status.DRAFT)

    def test_submit_action_requires_authentication(self):
        order = self.create_order(
            branch=self.branch,
            customer=self.customer,
            created_by=self.customer_user,
            status=ShipmentOrder.Status.DRAFT,
        )

        self.unauthenticate()

        response = self.client.post(
            reverse(
                "freight:freight-api-v1:shipment-order-submit",
                kwargs={"pk": order.pk},
            ),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 401)

    
    def test_branch_manager_can_view_order_status_history(self):
        order = self.create_order(
            branch=self.branch,
            customer=self.customer,
            created_by=self.customer_user,
            status=ShipmentOrder.Status.SUBMITTED,
        )

        ShipmentStatusHistory.objects.create(
            shipment=order,
            from_status=ShipmentOrder.Status.DRAFT,
            to_status=ShipmentOrder.Status.SUBMITTED,
            changed_by=self.customer_user,
            note="Customer submitted shipment order.",
        )

        self.authenticate(self.branch_manager)

        response = self.client.get(
            reverse(
                "freight:freight-api-v1:shipment-order-status-history",
                kwargs={"pk": order.pk},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["from_status"],
            ShipmentOrder.Status.DRAFT,
        )
        self.assertEqual(
            response.data[0]["to_status"],
            ShipmentOrder.Status.SUBMITTED,
        )
        self.assertEqual(
            response.data[0]["changed_by"],
            self.customer_user.id,
        )
        self.assertEqual(
            response.data[0]["note"],
            "Customer submitted shipment order.",
        )

    def test_customer_cannot_view_another_customers_status_history(self):
        order = self.create_order(
            branch=self.branch,
            customer=self.other_customer,
            created_by=self.other_customer_user,
        )

        self.authenticate(self.customer_user)

        response = self.client.get(
            reverse(
                "freight:freight-api-v1:shipment-order-status-history",
                kwargs={"pk": order.pk},
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_status_history_endpoint_requires_authentication(self):
        order = self.create_order(
            branch=self.branch,
            customer=self.customer,
            created_by=self.customer_user,
        )

        self.unauthenticate()

        response = self.client.get(
            reverse(
                "freight:freight-api-v1:shipment-order-status-history",
                kwargs={"pk": order.pk},
            )
        )

        self.assertEqual(response.status_code, 401)

    
    def test_operator_can_start_review(self):
        order = self.create_order(
            branch=self.branch,
            customer=self.customer,
            created_by=self.customer_user,
            status=ShipmentOrder.Status.SUBMITTED,
        )

        self.authenticate(self.operator)

        response = self.client.post(
            reverse(
                "freight:freight-api-v1:shipment-order-start-review",
                kwargs={"pk": order.pk},
            ),
            {"note": "Review started."},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        order.refresh_from_db()
        self.assertEqual(
            order.status,
            ShipmentOrder.Status.OPERATOR_REVIEW,
        )

        self.assertTrue(
            ShipmentStatusHistory.objects.filter(
                shipment=order,
                from_status=ShipmentOrder.Status.SUBMITTED,
                to_status=ShipmentOrder.Status.OPERATOR_REVIEW,
                changed_by=self.operator,
                note="Review started.",
            ).exists()
        )

    def test_operator_can_approve_collection(self):
        order = self.create_order(
            branch=self.branch,
            customer=self.customer,
            created_by=self.customer_user,
            status=ShipmentOrder.Status.OPERATOR_REVIEW,
        )

        self.authenticate(self.operator)

        response = self.client.post(
            reverse(
                "freight:freight-api-v1:shipment-order-approve-collection",
                kwargs={"pk": order.pk},
            ),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        order.refresh_from_db()
        self.assertEqual(
            order.status,
            ShipmentOrder.Status.APPROVED_FOR_COLLECTION,
        )

        self.assertTrue(
            ShipmentStatusHistory.objects.filter(
                shipment=order,
                from_status=ShipmentOrder.Status.OPERATOR_REVIEW,
                to_status=ShipmentOrder.Status.APPROVED_FOR_COLLECTION,
                changed_by=self.operator,
            ).exists()
        )

    def test_operator_can_reject_order_under_review(self):
        order = self.create_order(
            branch=self.branch,
            customer=self.customer,
            created_by=self.customer_user,
            status=ShipmentOrder.Status.OPERATOR_REVIEW,
        )

        self.authenticate(self.operator)

        response = self.client.post(
            reverse(
                "freight:freight-api-v1:shipment-order-reject",
                kwargs={"pk": order.pk},
            ),
            {"reason": "Invalid shipment details."},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        order.refresh_from_db()
        self.assertEqual(
            order.status,
            ShipmentOrder.Status.REJECTED,
        )

        self.assertTrue(
            ShipmentStatusHistory.objects.filter(
                shipment=order,
                from_status=ShipmentOrder.Status.OPERATOR_REVIEW,
                to_status=ShipmentOrder.Status.REJECTED,
                changed_by=self.operator,
                note="Invalid shipment details.",
            ).exists()
        )

    def test_operator_cannot_reject_order_outside_review(self):
        order = self.create_order(
            branch=self.branch,
            customer=self.customer,
            created_by=self.customer_user,
            status=ShipmentOrder.Status.SUBMITTED,
        )

        self.authenticate(self.operator)

        response = self.client.post(
            reverse(
                "freight:freight-api-v1:shipment-order-reject",
                kwargs={"pk": order.pk},
            ),
            {"reason": "Invalid details."},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        order.refresh_from_db()
        self.assertEqual(
            order.status,
            ShipmentOrder.Status.SUBMITTED,
        )

    def test_branch_manager_can_cancel_order(self):
        order = self.create_order(
            branch=self.branch,
            customer=self.customer,
            created_by=self.customer_user,
            status=ShipmentOrder.Status.SUBMITTED,
        )

        self.authenticate(self.branch_manager)

        response = self.client.post(
            reverse(
                "freight:freight-api-v1:shipment-order-cancel",
                kwargs={"pk": order.pk},
            ),
            {"note": "Cancelled by branch manager."},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        order.refresh_from_db()
        self.assertEqual(
            order.status,
            ShipmentOrder.Status.CANCELLED,
        )

        self.assertTrue(
            ShipmentStatusHistory.objects.filter(
                shipment=order,
                from_status=ShipmentOrder.Status.SUBMITTED,
                to_status=ShipmentOrder.Status.CANCELLED,
                changed_by=self.branch_manager,
                note="Cancelled by branch manager.",
            ).exists()
        )

    def test_operator_cannot_cancel_order_without_permission(self):
        order = self.create_order(
            branch=self.branch,
            customer=self.customer,
            created_by=self.customer_user,
            status=ShipmentOrder.Status.SUBMITTED,
        )

        self.authenticate(self.operator)

        response = self.client.post(
            reverse(
                "freight:freight-api-v1:shipment-order-cancel",
                kwargs={"pk": order.pk},
            ),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

        order.refresh_from_db()
        self.assertEqual(
            order.status,
            ShipmentOrder.Status.SUBMITTED,
        )

    def test_branch_manager_can_mark_invoiced_order_ready_for_dispatch(self):
        order = self.create_order(
            branch=self.branch,
            customer=self.customer,
            created_by=self.customer_user,
            status=ShipmentOrder.Status.INVOICE_REGISTERED,
        )

        self.authenticate(self.branch_manager)

        response = self.client.post(
            reverse(
                "freight:freight-api-v1:shipment-order-ready-for-dispatch",
                kwargs={"pk": order.pk},
            ),
            {"note": "Invoice checked."},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        order.refresh_from_db()
        self.assertEqual(
            order.status,
            ShipmentOrder.Status.READY_FOR_DISPATCH,
        )

        self.assertTrue(
            ShipmentStatusHistory.objects.filter(
                shipment=order,
                from_status=ShipmentOrder.Status.INVOICE_REGISTERED,
                to_status=ShipmentOrder.Status.READY_FOR_DISPATCH,
                changed_by=self.branch_manager,
                note="Invoice checked.",
            ).exists()
        )

    def test_cannot_mark_order_ready_for_dispatch_before_invoice_registration(self):
        order = self.create_order(
            branch=self.branch,
            customer=self.customer,
            created_by=self.customer_user,
            status=ShipmentOrder.Status.RECEIVED_AT_BRANCH,
        )

        self.authenticate(self.branch_manager)

        response = self.client.post(
            reverse(
                "freight:freight-api-v1:shipment-order-ready-for-dispatch",
                kwargs={"pk": order.pk},
            ),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        order.refresh_from_db()
        self.assertEqual(
            order.status,
            ShipmentOrder.Status.RECEIVED_AT_BRANCH,
        )

    def test_operator_without_change_permission_cannot_mark_order_ready_for_dispatch(self):
        order = self.create_order(
            branch=self.branch,
            customer=self.customer,
            created_by=self.customer_user,
            status=ShipmentOrder.Status.INVOICE_REGISTERED,
        )

        self.authenticate(self.operator)

        response = self.client.post(
            reverse(
                "freight:freight-api-v1:shipment-order-ready-for-dispatch",
                kwargs={"pk": order.pk},
            ),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

        order.refresh_from_db()
        self.assertEqual(
            order.status,
            ShipmentOrder.Status.INVOICE_REGISTERED,
        )

    def test_branch_manager_cannot_mark_other_branch_order_ready_for_dispatch(self):
        order = self.create_order(
            branch=self.other_branch,
            customer=self.customer,
            created_by=self.customer_user,
            status=ShipmentOrder.Status.INVOICE_REGISTERED,
        )

        self.authenticate(self.branch_manager)

        response = self.client.post(
            reverse(
                "freight:freight-api-v1:shipment-order-ready-for-dispatch",
                kwargs={"pk": order.pk},
            ),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 404)

        order.refresh_from_db()
        self.assertEqual(
            order.status,
            ShipmentOrder.Status.INVOICE_REGISTERED,
        )