from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from accounts.models import User
from freight.models import Customer


class CustomerRegistrationInvitationSerializer(
    serializers.Serializer
):
    invitation_token = serializers.CharField(
        required=True,
        write_only=True,
    )

    mobile = serializers.CharField(
        required=True,
        write_only=True,
    )

    password = serializers.CharField(
        min_length=6,
        max_length=68,
        write_only=True,
        required=True,
        style={
            "input_type": "password",
        },
    )

    password1 = serializers.CharField(
        min_length=6,
        max_length=68,
        write_only=True,
        required=True,
        style={
            "input_type": "password",
        },
    )

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

    def validate_mobile(self, value):
        try:
            return User.objects.normalize_mobile(value)
        except (ValueError, ValidationError) as exc:
            raise serializers.ValidationError(
                str(exc)
            )

    def validate(self, attrs):
        if attrs["password"] != attrs["password1"]:
            raise serializers.ValidationError(
                {
                    "details": "Passwords does not match"
                }
            )

        try:
            validate_password(
                attrs["password"]
            )
        except ValidationError as exc:
            raise serializers.ValidationError(
                {
                    "password": list(exc.messages)
                }
            )

        return attrs