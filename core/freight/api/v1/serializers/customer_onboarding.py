from rest_framework import serializers

from freight.models import Customer


class CustomerOnboardingSerializer(serializers.Serializer):
    customer_type = serializers.ChoiceField(
        choices=Customer.CustomerType.choices,
    )

    first_name = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    last_name = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    national_id = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    company_name = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    company_registration_no = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    economic_code = serializers.CharField(
        required=False,
        allow_blank=True,
    )