from rest_framework import serializers

from accounts.models import User
from freight.models import (
    DispatchBatch,
    DispatchFreightAssignment,
    DispatchOrder,
)


class DispatchFreightAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DispatchFreightAssignment
        fields = [
            "id",
            "dispatch_order",
            "freight_company",
            "status",
            "payer",
            "freight_amount",
            "rejection_reason",
            "freight_invoice_number",
            "freight_invoice_file",
            "notes",
            "assigned_at",
            "approved_at",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "freight_amount",
            "rejection_reason",
            "assigned_at",
            "approved_at",
            "created_by",
            "created_at",
            "updated_at",
        ]


class DispatchOrderSerializer(serializers.ModelSerializer):
    freight_assignments = DispatchFreightAssignmentSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = DispatchOrder
        fields = [
            "id",
            "batch",
            "order",
            "status",
            "notes",
            "freight_assignments",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "notes",
            "freight_assignments",
            "created_at",
            "updated_at",
        ]


class DispatchBatchSerializer(serializers.ModelSerializer):
    orders = DispatchOrderSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = DispatchBatch
        fields = [
            "id",
            "branch",
            "dispatcher",
            "status",
            "scheduled_at",
            "dispatched_at",
            "completed_at",
            "notes",
            "created_by",
            "created_at",
            "updated_at",
            "orders",
        ]
        read_only_fields = [
            "id",
            "status",
            "dispatcher",
            "dispatched_at",
            "completed_at",
            "created_by",
            "created_at",
            "updated_at",
            "orders",
        ]


class DispatchBatchCreateSerializer(serializers.Serializer):
    branch = serializers.IntegerField()
    scheduled_at = serializers.DateTimeField(
        required=False,
        allow_null=True,
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
    )


class DispatchOrderCreateSerializer(serializers.Serializer):
    order = serializers.IntegerField()


class DispatchAssignDispatcherSerializer(serializers.Serializer):
    dispatcher = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
    )


class DispatchFreightAssignmentCreateSerializer(serializers.Serializer):
    freight_company = serializers.IntegerField()

    payer = serializers.ChoiceField(
        choices=DispatchFreightAssignment.Payer.choices,
    )


class DispatchStatusSerializer(serializers.Serializer):
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
    )


class DispatchRejectSerializer(serializers.Serializer):
    reason = serializers.CharField()

    notes = serializers.CharField(
        required=False,
        allow_blank=True,
    )


class DispatchDeliveredSerializer(serializers.Serializer):
    freight_invoice_number = serializers.CharField()

    freight_invoice_file = serializers.FileField(
        required=False,
        allow_null=True,
    )

    notes = serializers.CharField(
        required=False,
        allow_blank=True,
    )