from rest_framework import serializers

from freight.models import (
    Branch,
    CustomerBranchMembership,
)


class CustomerBranchMembershipRequestSerializer(
    serializers.Serializer
):
    branch = serializers.PrimaryKeyRelatedField(
        queryset=Branch.objects.filter(is_active=True),
    )


class CustomerBranchMembershipSerializer(
    serializers.ModelSerializer
):
    branch = serializers.SerializerMethodField()

    class Meta:
        model = CustomerBranchMembership
        fields = [
            "id",
            "branch",
            "status",
            "created_at",
            "approved_at",
        ]
        read_only_fields = [
            "id",
            "branch",
            "status",
            "created_at",
            "approved_at",
        ]

    def get_branch(self, obj):
        return {
            "id": obj.branch_id,
            "name": obj.branch.name,
        }