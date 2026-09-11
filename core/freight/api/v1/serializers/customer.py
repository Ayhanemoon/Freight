from rest_framework import serializers

from freight.models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    mobile = serializers.CharField(
        source="user.mobile",
        read_only=True,
    )

    display_name = serializers.CharField(
        read_only=True,
    )

    class Meta:
        model = Customer
        fields = [
            "id",
            "mobile",
            "customer_type",
            "first_name",
            "last_name",
            "national_id",
            "company_name",
            "company_registration_no",
            "economic_code",
            "display_name",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "mobile",
            "display_name",
            "created_at",
        ]