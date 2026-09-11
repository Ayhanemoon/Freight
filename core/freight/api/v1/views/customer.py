from rest_framework.viewsets import ModelViewSet

from freight.api.v1.serializers import CustomerSerializer
from freight.models import Customer


class CustomerViewSet(ModelViewSet):
    queryset = Customer.objects.select_related("user").all()
    serializer_class = CustomerSerializer