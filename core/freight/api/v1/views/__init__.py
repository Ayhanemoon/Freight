from .branch import BranchViewSet
from .customer import CustomerViewSet
from .freight_company import FreightCompanyViewSet
from .shipment_order import ShipmentOrderViewSet
from .parcel import ParcelViewSet
from .invoice import InvoiceViewSet
from .invoice_charge import (
    InvoiceChargeCreateAPIView,
    InvoiceChargeDetailAPIView,
)