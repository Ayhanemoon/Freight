
from rest_framework import serializers

from freight.models import (
    Branch,
    Customer,
    FreightCompany,
    ShipmentOrder,
)
from freight.api.v1.serializers.branch import BranchSerializer
from freight.api.v1.serializers.customer import CustomerSerializer
from freight.api.v1.serializers.freight_company import (
    FreightCompanySerializer,
)



class NestedPrimaryKeyRelatedField(
    serializers.PrimaryKeyRelatedField
):
    def __init__(self, *args, serializer_class=None, **kwargs):
        self.serializer_class = serializer_class
        super().__init__(*args, **kwargs)

    def use_pk_only_optimization(self):
        return False

    def to_representation(self, value):
        return self.serializer_class(
            value,
            context=self.context,
        ).data


class ShipmentOrderSerializer(serializers.ModelSerializer):
    branch = NestedPrimaryKeyRelatedField(
        queryset=Branch.objects.all(),
        serializer_class=BranchSerializer,
    )

    customer = NestedPrimaryKeyRelatedField(
        queryset=Customer.objects.all(),
        serializer_class=CustomerSerializer,
        required=False,
    )

    preferred_freight_company = NestedPrimaryKeyRelatedField(
        queryset=FreightCompany.objects.all(),
        serializer_class=FreightCompanySerializer,
        required=False,
        allow_null=True,
    )

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

        extra_kwargs = {
            "customer": {"required": False},
        }

class ShipmentOrderListSerializer(ShipmentOrderSerializer):
    branch = serializers.PrimaryKeyRelatedField(
        read_only=True,
    )

    customer = serializers.PrimaryKeyRelatedField(
        read_only=True,
    )

    preferred_freight_company = serializers.PrimaryKeyRelatedField(
        read_only=True,
    )

class ShipmentOrderActionSerializer(serializers.Serializer):
    note = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=2000,
    )


class ShipmentOrderRejectSerializer(serializers.Serializer):
    reason = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=2000,
    )