from rest_framework import serializers

from freight.models import (
    InvoiceCharge,
    Parcel,
    ShipmentOrder,
)


class InvoiceChargeInputSerializer(serializers.Serializer):
    charge_type = serializers.ChoiceField(
        choices=InvoiceCharge.ChargeType.choices,
    )

    payer = serializers.ChoiceField(
        choices=InvoiceCharge.Payer.choices,
        required=False,
        allow_null=True,
        allow_blank=True,
    )

    description = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0,
    )


class InvoiceParcelInputSerializer(serializers.Serializer):
    parcel = serializers.PrimaryKeyRelatedField(
        queryset=Parcel.objects.all(),
    )

    parcel_name = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    parcel_type = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    quantity = serializers.IntegerField(
        required=False,
        min_value=1,
        default=1,
    )


class InvoiceCreateSerializer(serializers.Serializer):
    order = serializers.PrimaryKeyRelatedField(
        queryset=ShipmentOrder.objects.all(),
    )

    invoice_number = serializers.CharField(
        max_length=50,
    )

    issued_at = serializers.DateTimeField(
        required=False,
        allow_null=True,
    )

    charges = InvoiceChargeInputSerializer(
        many=True,
        required=False,
        default=list,
    )

    parcels = InvoiceParcelInputSerializer(
        many=True,
        required=True,
    )

    notes = serializers.CharField(
        required=False,
        allow_blank=True,
    )