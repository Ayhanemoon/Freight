from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.utils import timezone
from rest_framework.test import APITestCase

from freight.models import (
    Branch,
    Customer,
    FreightCompany,
    Invoice,
    InvoiceCharge,
    ShipmentOrder,
)


User = get_user_model()


class FreightAPITestCase(APITestCase):
    """
    Shared base class for Freight API integration tests.
    """

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def unauthenticate(self):
        self.client.force_authenticate(user=None)

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    def create_user(
        self,
        mobile="09121234567",
        password="test@123456",
        branch=None,
        is_staff=False,
        is_superuser=False,
        is_mobile_verified=True,
        is_active=True,
        email=None,
    ):
        if email is None:
            email = "{}@example.com".format(
                mobile.replace("+", "").replace(" ", "")
            )

        return User.objects.create_user(
            mobile=mobile,
            password=password,
            email=email,
            branch=branch,
            is_staff=is_staff,
            is_superuser=is_superuser,
            is_mobile_verified=is_mobile_verified,
            is_active=is_active,
        )

    def grant_permission(self, user, permission_codename):
        """
        Grant a Freight model permission directly to a user.

        Example:
            self.grant_permission(
                self.operator,
                "add_dispatchbatch",
            )
        """
        permission = Permission.objects.get(
            codename=permission_codename,
        )
        user.user_permissions.add(permission)
        return permission

    # ------------------------------------------------------------------
    # Branch
    # ------------------------------------------------------------------

    def create_branch(
        self,
        name="Tehran Branch",
        code="THR",
        city="Tehran",
        address="Test address",
        phone="02112345678",
        is_active=True,
    ):
        return Branch.objects.create(
            name=name,
            code=code,
            city=city,
            address=address,
            phone=phone,
            is_active=is_active,
        )

    # ------------------------------------------------------------------
    # Customer
    # ------------------------------------------------------------------

    def create_customer(
        self,
        user=None,
        customer_type=Customer.CustomerType.PERSON,
        first_name="Test",
        last_name="Customer",
        national_id="0012345678",
        company_name="",
        company_registration_no="",
        economic_code="",
    ):
        if user is None:
            user = self.create_user(
                mobile="09121111111",
                email="customer@example.com",
            )

        return Customer.objects.create(
            user=user,
            customer_type=customer_type,
            first_name=first_name,
            last_name=last_name,
            national_id=national_id,
            company_name=company_name,
            company_registration_no=company_registration_no,
            economic_code=economic_code,
        )

    # ------------------------------------------------------------------
    # Freight company
    # ------------------------------------------------------------------

    def create_freight_company(
        self,
        name="Test Freight Company",
        code="TFC",
        contact_phone="02122222222",
        website="",
        is_active=True,
    ):
        return FreightCompany.objects.create(
            name=name,
            code=code,
            contact_phone=contact_phone,
            website=website,
            is_active=is_active,
        )

    # ------------------------------------------------------------------
    # Shipment order
    # ------------------------------------------------------------------

    def create_order(
        self,
        branch,
        customer,
        created_by=None,
        preferred_freight_company=None,
        status=ShipmentOrder.Status.READY_FOR_DISPATCH,
        sender_name="Test Sender",
        sender_mobile="09123333333",
        sender_address="Sender address",
        receiver_name="Test Receiver",
        receiver_mobile="09124444444",
        receiver_address="Receiver address",
        shipment_description="Test shipment",
    ):
        return ShipmentOrder.objects.create(
            branch=branch,
            customer=customer,
            preferred_freight_company=preferred_freight_company,
            sender_name=sender_name,
            sender_mobile=sender_mobile,
            sender_address=sender_address,
            receiver_name=receiver_name,
            receiver_mobile=receiver_mobile,
            receiver_address=receiver_address,
            shipment_description=shipment_description,
            status=status,
            created_by=created_by,
        )

    # ------------------------------------------------------------------
    # Invoice
    # ------------------------------------------------------------------

    def create_invoice(
        self,
        order,
        operator,
        invoice_number="INV-TEST-001",
        customer_name="Test Customer",
        customer_mobile="09121111111",
        customer_address="Customer address",
        receiver_name="Test Receiver",
        receiver_mobile="09124444444",
        receiver_address="Receiver address",
        total_cost=Decimal("0.00"),
        notes="",
    ):
        return Invoice.objects.create(
            order=order,
            invoice_number=invoice_number,
            issued_at=timezone.now(),
            operator=operator,
            customer_name=customer_name,
            customer_mobile=customer_mobile,
            customer_address=customer_address,
            receiver_name=receiver_name,
            receiver_mobile=receiver_mobile,
            receiver_address=receiver_address,
            total_cost=total_cost,
            notes=notes,
        )

    # ------------------------------------------------------------------
    # Invoice charges
    # ------------------------------------------------------------------

    def create_invoice_charge(
        self,
        invoice,
        charge_type=InvoiceCharge.ChargeType.FREIGHT,
        amount=Decimal("100000.00"),
        payer=InvoiceCharge.Payer.SENDER,
        description="Test charge",
    ):
        return InvoiceCharge.objects.create(
            invoice=invoice,
            charge_type=charge_type,
            payer=payer,
            description=description,
            amount=amount,
        )

    def create_invoice_with_charges(
        self,
        order,
        operator,
        charges=None,
        invoice_number="INV-TEST-001",
    ):
        """
        Create an invoice and calculate total_cost from all charges.

        This intentionally reflects the business rule:
        Invoice.total_cost = sum(InvoiceCharge.amount)
        """

        invoice = self.create_invoice(
            order=order,
            operator=operator,
            invoice_number=invoice_number,
            total_cost=Decimal("0.00"),
        )

        if charges is None:
            charges = [
                {
                    "charge_type": InvoiceCharge.ChargeType.FREIGHT,
                    "amount": Decimal("100000.00"),
                    "payer": InvoiceCharge.Payer.SENDER,
                },
            ]

        total = Decimal("0.00")

        for charge_data in charges:
            charge = self.create_invoice_charge(
                invoice=invoice,
                **charge_data,
            )
            total += charge.amount

        invoice.total_cost = total
        invoice.save(update_fields=["total_cost"])

        return invoice