
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
