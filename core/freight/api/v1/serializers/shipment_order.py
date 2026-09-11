from rest_framework import serializers

from freight.models import ShipmentOrder


class ShipmentOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShipmentOrder
        fields = [
            "id",
            "public_id",
            "tracking_code",
            "barcode",

            "branch",
            "customer",
            "preferred_freight_company",

            "sender_name",
            "sender_mobile",
            "sender_address",

            "receiver_name",
            "receiver_mobile",
            "receiver_address",

            "shipment_description",

            "status",
            "submitted_at",

            "created_by",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "public_id",
            "tracking_code",
            "barcode",
            "status",
            "submitted_at",
            "created_by",
            "created_at",
            "updated_at",
        ]