from rest_framework import serializers

from freight.models import FreightCompany


class FreightCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = FreightCompany
        fields = [
            "id",
            "name",
            "code",
            "contact_phone",
            "website",
            "is_active",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
        ]