from rest_framework import serializers

from freight.models import Invoice


class InvoiceSerializer(serializers.ModelSerializer):
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
            "total_cost",
            "created_at",
            "updated_at",
        ]