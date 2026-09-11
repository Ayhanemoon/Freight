from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound

from freight.api.v1.serializers import InvoiceChargeSerializer
from freight.models import Invoice, InvoiceCharge
from freight.services.invoice_charge import (
    create_invoice_charge,
    update_invoice_charge,
    delete_invoice_charge,
)


class InvoiceChargeCreateAPIView(APIView):
    def post(self, request, invoice_id):
        try:
            invoice = Invoice.objects.select_related(
                "order",
                "order__branch",
            ).get(pk=invoice_id)
        except Invoice.DoesNotExist:
            raise NotFound("Invoice not found.")

        serializer = InvoiceChargeSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        charge = create_invoice_charge(
            invoice=invoice,
            created_by=request.user,
            charge_type=data["charge_type"],
            amount=data["amount"],
            payer=data.get("payer"),
            description=data.get("description", ""),
        )

        return Response(
            InvoiceChargeSerializer(charge).data,
            status=status.HTTP_201_CREATED,
        )


class InvoiceChargeDetailAPIView(APIView):
    def _get_charge(self, invoice_id, charge_id):
        try:
            return InvoiceCharge.objects.select_related(
                "invoice",
                "invoice__order",
                "invoice__order__branch",
            ).get(
                pk=charge_id,
                invoice_id=invoice_id,
            )
        except InvoiceCharge.DoesNotExist:
            raise NotFound("Invoice charge not found.")

    def patch(self, request, invoice_id, charge_id):
        charge = self._get_charge(
            invoice_id,
            charge_id,
        )

        serializer = InvoiceChargeSerializer(
            charge,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        charge = update_invoice_charge(
            charge=charge,
            updated_by=request.user,
            charge_type=data.get("charge_type"),
            amount=data.get("amount"),
            payer=data.get("payer"),
            description=data.get("description"),
        )

        return Response(
            InvoiceChargeSerializer(charge).data,
        )

    def delete(self, request, invoice_id, charge_id):
        charge = self._get_charge(
            invoice_id,
            charge_id,
        )

        delete_invoice_charge(
            charge=charge,
            deleted_by=request.user,
        )

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )