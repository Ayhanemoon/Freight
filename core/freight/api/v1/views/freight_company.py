from rest_framework.viewsets import ModelViewSet

from freight.api.v1.serializers import FreightCompanySerializer
from freight.models import FreightCompany


class FreightCompanyViewSet(ModelViewSet):
    queryset = FreightCompany.objects.all()
    serializer_class = FreightCompanySerializer