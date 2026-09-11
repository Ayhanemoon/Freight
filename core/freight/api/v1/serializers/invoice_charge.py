from rest_framework import serializers

from freight.models import InvoiceCharge


class InvoiceChargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceCharge
        fields = [
            "id",
            "invoice",
            "charge_type",
            "payer",
            "description",
            "amount",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
        ]

        extra_kwargs = {
            "payer": {
                "required": False,
                "allow_null": True,
                "allow_blank": True,
            },
        }

    def validate_amount(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Invoice charge amount cannot be negative."
            )

        return value