
from rest_framework import serializers

from freight.models import Invoice, InvoiceCharge, InvoiceParcel


class InvoiceChargeReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceCharge
        fields = [
            "id",
            "charge_type",
            "payer",
            "description",
            "amount",
            "created_at",
        ]
        read_only_fields = fields


class InvoiceParcelReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceParcel
        fields = [
            "id",
            "parcel",
            "parcel_number",
            "parcel_name",
            "parcel_type",
            "quantity",
            "created_at",
        ]
        read_only_fields = fields


class InvoiceSerializer(serializers.ModelSerializer):
    charges = InvoiceChargeReadSerializer(
        many=True,
        read_only=True,
    )
    parcels = InvoiceParcelReadSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Invoice
        fields = [
            "id",
            "order",
            "invoice_number",
            "issued_at",
            "operator",
            "customer_name",
            "customer_mobile",
            "customer_address",
            "receiver_name",
            "receiver_mobile",
            "receiver_address",
            "charges",
            "parcels",
            "total_cost",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "operator",
            "customer_name",
            "customer_mobile",
            "customer_address",
            "receiver_name",
            "receiver_mobile",
            "receiver_address",
            "charges",
            "parcels",
            "total_cost",
            "created_at",
            "updated_at",
        ]



class InvoiceUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = [
            "invoice_number",
            "notes",
        ]

    def to_internal_value(self, data):
        allowed_fields = set(self.fields.keys())
        submitted_fields = set(data.keys())
        unexpected_fields = submitted_fields - allowed_fields

        if unexpected_fields:
            raise serializers.ValidationError({
                field: "This field cannot be updated."
                for field in sorted(unexpected_fields)
            })

        return super().to_internal_value(data)

    def validate_invoice_number(self, value):
        queryset = Invoice.objects.filter(
            invoice_number=value,
        )

        if self.instance:
            queryset = queryset.exclude(
                pk=self.instance.pk,
            )

        if queryset.exists():
            raise serializers.ValidationError(
                "An invoice with this number already exists."
            )

        return value
