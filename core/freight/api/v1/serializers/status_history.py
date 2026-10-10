
from rest_framework import serializers

from freight.models import ShipmentStatusHistory


class ShipmentStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ShipmentStatusHistory
        fields = [
            "id",
            "shipment",
            "from_status",
            "to_status",
            "changed_by",
            "note",
            "created_at",
        ]
        read_only_fields = fields