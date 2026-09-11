from rest_framework import serializers

from freight.models import Parcel


class ParcelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parcel
        fields = [
            "id",
            "order",
            "parcel_number",

            "declared_weight_kg",
            "declared_length_cm",
            "declared_width_cm",
            "declared_height_cm",
            "contents_description",

            "verified_weight_kg",
            "verified_length_cm",
            "verified_width_cm",
            "verified_height_cm",
            "verification_status",
            "verified_by",
            "verified_at",

            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "verification_status",
            "verified_by",
            "verified_at",
            "created_at",
            "updated_at",
        ]