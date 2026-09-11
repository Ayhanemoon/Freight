from django.contrib.auth import get_user_model

from rest_framework import serializers

from freight.models import CollectionTask, Parcel

User = get_user_model()


class CollectionTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollectionTask
        fields = [
            "id",
            "order",
            "task_type",
            "status",
            "collector",
            "scheduled_at",
            "started_at",
            "completed_at",
            "notes",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "status",
            "collector",
            "started_at",
            "completed_at",
            "created_at",
            "updated_at",
        ]


class CollectionTaskAssignSerializer(serializers.Serializer):
    collector = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
    )


class CollectionTaskStatusSerializer(serializers.Serializer):
    note = serializers.CharField(
        required=False,
        allow_blank=True,
    )


class CollectionTaskVerifyParcelSerializer(serializers.Serializer):
    parcel = serializers.PrimaryKeyRelatedField(
        queryset=Parcel.objects.all(),
    )

    verified_weight_kg = serializers.DecimalField(
        max_digits=8,
        decimal_places=2,
        min_value=0,
    )

    verified_length_cm = serializers.DecimalField(
        max_digits=8,
        decimal_places=2,
        min_value=0,
    )

    verified_width_cm = serializers.DecimalField(
        max_digits=8,
        decimal_places=2,
        min_value=0,
    )

    verified_height_cm = serializers.DecimalField(
        max_digits=8,
        decimal_places=2,
        min_value=0,
    )