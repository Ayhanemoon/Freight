from decimal import Decimal

from django.urls import reverse
from rest_framework import status

from freight.models import Invoice, Parcel, ShipmentOrder

from .base import FreightAPITestCase


class InvoiceAPITests(FreightAPITestCase):
    def setUp(self):
        self.branch = self.create_branch(
            name="Tehran Branch",
            code="THR",
        )

        self.other_branch = self.create_branch(
            name="Mashhad Branch",
            code="MHD",
        )

        self.operator = self.create_user(
            mobile="09120001001",
            branch=self.branch,
            is_staff=True,
        )

        self.other_branch_user = self.create_user(
            mobile="09120001002",
            branch=self.other_branch,
            is_staff=True,
        )

        self.customer = self.create_customer(
            user=self.create_user(
                mobile="09120001003",
            )
        )

        self.other_customer = self.create_customer(
            user=self.create_user(
                mobile="09120001004",
            )
        )

        self.order = self.create_order(
            branch=self.branch,
            customer=self.customer,
            created_by=self.operator,
            status=ShipmentOrder.Status.RECEIVED_AT_BRANCH,
        )

        self.create_order_instance = self.create_order(
            branch=self.branch,
            customer=self.customer,
            created_by=self.operator,
            status=ShipmentOrder.Status.RECEIVED_AT_BRANCH,
        )

        self.create_order_instance_parcel = Parcel.objects.create(
            order=self.create_order_instance,
            parcel_number=1,
            declared_weight_kg=10,
            declared_length_cm=30,
            declared_width_cm=20,
            declared_height_cm=15,
        )

        self.other_order = self.create_order(
            branch=self.other_branch,
            customer=self.other_customer,
            created_by=self.other_branch_user,
            status=ShipmentOrder.Status.READY_FOR_DISPATCH,
        )

        self.invoice = self.create_invoice_with_charges(
            order=self.order,
            operator=self.operator,
            invoice_number="INV-THR-001",
        )

        self.other_invoice = self.create_invoice_with_charges(
            order=self.other_order,
            operator=self.other_branch_user,
            invoice_number="INV-MHD-001",
        )

        self.list_url = reverse(
            "freight:freight-api-v1:invoice-list",
        )

        self.detail_url = reverse(
            "freight:freight-api-v1:invoice-detail",
            kwargs={"pk": self.invoice.pk},
        )

        self.other_detail_url = reverse(
            "freight:freight-api-v1:invoice-detail",
            kwargs={"pk": self.other_invoice.pk},
        )

        self.authenticate(self.operator)

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def test_unauthenticated_user_cannot_list_invoices(self):
        self.unauthenticate()

        response = self.client.get(self.list_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_unauthenticated_user_cannot_retrieve_invoice(self):
        self.unauthenticate()

        response = self.client.get(self.detail_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    # ------------------------------------------------------------------
    # List / branch isolation
    # ------------------------------------------------------------------

    def test_user_only_sees_invoices_from_own_branch(self):
        response = self.client.get(self.list_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        returned_ids = {
            item["id"]
            for item in response.data["results"]
        }

        self.assertIn(
            self.invoice.id,
            returned_ids,
        )

        self.assertNotIn(
            self.other_invoice.id,
            returned_ids,
        )

    # ------------------------------------------------------------------
    # Retrieve / branch isolation
    # ------------------------------------------------------------------

    def test_user_can_retrieve_own_branch_invoice(self):
        response = self.client.get(
            self.detail_url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["id"],
            self.invoice.id,
        )

    def test_user_cannot_retrieve_other_branch_invoice(self):
        response = self.client.get(
            self.other_detail_url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    # ------------------------------------------------------------------
    # Create authorization
    # ------------------------------------------------------------------

    def test_user_without_invoice_permission_cannot_create_invoice(self):
        response = self.client.post(
            self.list_url,
            {
                "order": self.create_order_instance.id,
                "invoice_number": "INV-NEW-001",
                "parcels": [],
                "charges": [
                    {
                        "charge_type": "freight",
                        "amount": "100000.00",
                        "payer": "sender",
                        "description": "Freight",
                    },
                ],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_user_with_invoice_permission_can_create_invoice(self):
        self.grant_permission(
            self.operator,
            "add_invoice",
        )

        response = self.client.post(
            self.list_url,
            {
                "order": self.create_order_instance.id,
                "invoice_number": "INV-NEW-002",
                "parcels": [
                    {
                        "parcel": self.create_order_instance_parcel.id,
                        "parcel_name": "Test Parcel",
                        "parcel_type": "Box",
                        "quantity": 1,
                    }
                ],
                "charges": [
                    {
                        "charge_type": "freight",
                        "amount": "100000.00",
                        "payer": "sender",
                        "description": "Freight",
                    },
                ],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        invoice = Invoice.objects.get(
            invoice_number="INV-NEW-002",
        )

        self.assertEqual(
            invoice.order_id,
            self.create_order_instance.id,
        )

        self.assertEqual(
            invoice.operator_id,
            self.operator.id,
        )

        self.assertEqual(
            invoice.total_cost,
            Decimal("100000.00"),
        )

        self.assertEqual(
            invoice.charges.count(),
            1,
        )

        self.assertEqual(
            invoice.parcels.count(),
            1,
        )

        self.create_order_instance.refresh_from_db()

        self.assertEqual(
            self.create_order_instance.status,
            ShipmentOrder.Status.INVOICE_REGISTERED,
        )