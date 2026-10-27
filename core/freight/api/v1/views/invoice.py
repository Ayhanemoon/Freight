
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.mixins import (
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from freight.api.v1.serializers import (
    InvoiceCreateSerializer,
    InvoiceSerializer,
    InvoiceUpdateSerializer,
)
from freight.models import Invoice
from freight.permissions.capabilities import (
    has_branch_admin_capability,
    has_permission,
)
from freight.services.invoice import create_invoice


class InvoiceViewSet(
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    GenericViewSet,
):
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]

    # Allow PATCH but deliberately disable PUT and DELETE.
    http_method_names = [
        "get",
        "post",
        "patch",
        "head",
        "options",
    ]

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

    def get_serializer_class(self):
        if self.action in ("update", "partial_update"):
            return InvoiceUpdateSerializer

        return InvoiceSerializer

    def create(self, request, *args, **kwargs):
        input_serializer = InvoiceCreateSerializer(
            data=request.data,
        )
        input_serializer.is_valid(raise_exception=True)

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

        output_serializer = InvoiceSerializer(
            invoice,
            context=self.get_serializer_context(),
        )

        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    def perform_update(self, serializer):
        user = self.request.user

        if not user.is_active:
            raise PermissionDenied(
                "Your account is inactive."
            )

        # Branch managers and superusers can update invoices
        # within their permitted scope. Other users need the
        # specific change_invoice permission.
        if not (
            has_branch_admin_capability(user)
            or has_permission(user, "freight.change_invoice")
        ):
            raise PermissionDenied(
                "You do not have permission to update invoices."
            )

        serializer.save()
