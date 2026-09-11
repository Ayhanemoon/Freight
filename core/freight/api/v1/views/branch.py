from rest_framework.viewsets import ModelViewSet

from freight.models import Branch
from freight.api.v1.serializers import BranchSerializer


class BranchViewSet(ModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer