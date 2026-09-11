from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import (
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
)

from freight.api.v1.serializers import (
    InvoiceChargeSerializer,
    InvoiceCreateSerializer,
    InvoiceSerializer,
)
from freight.models import Invoice, InvoiceCharge
from freight.services.invoice import create_invoice
from freight.services.invoice_charge import (
    create_invoice_charge,
    update_invoice_charge,
    delete_invoice_charge,
)


class InvoiceViewSet(
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    GenericViewSet,
):
    serializer_class = InvoiceSerializer

    queryset = (
        Invoice.objects
        .select_related(
            "order",
            "order__branch",
            "order__customer",
            "order__customer__user",
            "operator",
        )
        .prefetch_related(
            "charges",
            "parcels",
        )
        .all()
    )

    def get_queryset(self):
        queryset = super().get_queryset()

        user = self.request.user

        if user.is_superuser:
            return queryset

        return queryset.filter(
            order__branch_id=user.branch_id,
        )

    def create(self, request, *args, **kwargs):
        input_serializer = InvoiceCreateSerializer(
            data=request.data,
        )

        input_serializer.is_valid(
            raise_exception=True,
        )

        data = input_serializer.validated_data

        invoice = create_invoice(
            order=data["order"],
            operator=request.user,
            invoice_number=data["invoice_number"],
            issued_at=data.get("issued_at"),
            charges=data.get("charges", []),
            parcels=data["parcels"],
            notes=data.get("notes", ""),
        )

        output_serializer = InvoiceSerializer(invoice)

        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="charges",
    )
    def create_charge(self, request, pk=None):
        invoice = self.get_object()

        serializer = InvoiceChargeSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        data = serializer.validated_data

        charge = create_invoice_charge(
            invoice=invoice,
            created_by=request.user,
            charge_type=data["charge_type"],
            amount=data["amount"],
            payer=data.get("payer"),
            description=data.get("description", ""),
        )

        output_serializer = InvoiceChargeSerializer(charge)

        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["patch"],
        url_path=r"charges/(?P<charge_id>[^/.]+)",
    )
    def update_charge(self, request, pk=None, charge_id=None):
        invoice = self.get_object()

        try:
            charge = invoice.charges.get(
                pk=charge_id,
            )
        except InvoiceCharge.DoesNotExist:
            raise NotFound(
                "Invoice charge not found."
            )

        serializer = InvoiceChargeSerializer(
            charge,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        data = serializer.validated_data

        charge = update_invoice_charge(
            charge=charge,
            updated_by=request.user,
            charge_type=data.get("charge_type"),
            amount=data.get("amount"),
            payer=data.get("payer"),
            description=data.get("description"),
        )

        output_serializer = InvoiceChargeSerializer(charge)

        return Response(
            output_serializer.data,
        )

    @action(
        detail=True,
        methods=["delete"],
        url_path=r"charges/(?P<charge_id>[^/.]+)",
    )
    def delete_charge(self, request, pk=None, charge_id=None):
        invoice = self.get_object()

        try:
            charge = invoice.charges.get(
                pk=charge_id,
            )
        except InvoiceCharge.DoesNotExist:
            raise NotFound(
                "Invoice charge not found."
            )

        delete_invoice_charge(
            charge=charge,
            deleted_by=request.user,
        )

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )