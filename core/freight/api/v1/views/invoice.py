from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import (
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
)

from freight.api.v1.serializers import (
    InvoiceCreateSerializer,
    InvoiceSerializer,
)
from freight.models import Invoice
from freight.services.invoice import create_invoice


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