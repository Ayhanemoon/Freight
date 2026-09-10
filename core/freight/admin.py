from django.contrib import admin

from freight.models import (
    Branch,
    CollectionTask,
    Customer,
    FreightCompany,
    ShipmentOrder,
    ShipmentStatusHistory,
    Parcel,
    Invoice,
    InvoiceCharge,
    InvoiceParcel,
    DispatchBatch,
    DispatchOrder,
    DispatchFreightAssignment,
)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'city', 'is_active')
    search_fields = ('name', 'code', 'city')
    list_filter = ('is_active', 'city')


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        'display_name',
        'customer_type',
        'user',
        'created_at',
    )

    list_filter = ('customer_type',)

    search_fields = (
        'first_name',
        'last_name',
        'company_name',
        'national_id',
        'company_registration_no',
        'user__mobile',
    )


@admin.register(FreightCompany)
class FreightCompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active')
    search_fields = ('name', 'code')
    list_filter = ('is_active',)


class ParcelInline(admin.TabularInline):
    model = Parcel
    extra = 0
    fields = (
        "parcel_number",
        "declared_weight_kg",
        "declared_length_cm",
        "declared_width_cm",
        "declared_height_cm",
        "contents_description",
        "verification_status",
        "verified_weight_kg",
        "verified_length_cm",
        "verified_width_cm",
        "verified_height_cm",
    )

@admin.register(ShipmentOrder)
class ShipmentOrderAdmin(admin.ModelAdmin):
    list_display = (
        'tracking_code',
        'branch',
        'customer',
        'receiver_name',
        'status',
        'submitted_at',
    )

    list_filter = (
        'branch',
        'status',
        'preferred_freight_company',
    )

    search_fields = (
        'tracking_code',
        'barcode',
        'sender_name',
        'receiver_name',
        'sender_mobile',
        'receiver_mobile',
    )

    readonly_fields = (
        'tracking_code',
        'barcode',
        'public_id',
        'created_at',
        'updated_at',
    )

    inlines = [ParcelInline]

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "invoice_number",
        "order",
        "operator",
        "issued_at",
        "total_cost",
    )
    search_fields = (
        "invoice_number",
        "order__tracking_code",
        "customer_name",
        "receiver_name",
    )
    list_filter = ("issued_at",)

@admin.register(InvoiceCharge)
class InvoiceChargeAdmin(admin.ModelAdmin):
    list_display = (
        "invoice",
        "charge_type",
        "amount",
    )
    search_fields = (
        "invoice__invoice_number",
        "charge_type",
    )
    list_filter = ("charge_type",)

@admin.register(InvoiceParcel)
class InvoiceParcelAdmin(admin.ModelAdmin):
    list_display = (
        "invoice",
        "parcel",
    )
    search_fields = (
        "invoice__invoice_number",
        "parcel__parcel_number",
    )

@admin.register(CollectionTask)
class CollectionTaskAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "task_type",
        "status",
        "collector",
        "scheduled_at",
        "created_at",
    )

    list_filter = (
        "task_type",
        "status",
    )

    search_fields = (
        "order__tracking_code",
        "order__barcode",
        "collector__mobile",
    )

    autocomplete_fields = (
        "order",
        "collector",
    )

@admin.register(ShipmentStatusHistory)
class ShipmentStatusHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "shipment",
        "from_status",
        "to_status",
        "changed_by",
        "created_at",
    )

    list_filter = (
        "from_status",
        "to_status",
    )

    search_fields = (
        "shipment__tracking_code",
        "shipment__barcode",
        "changed_by__mobile",
    )

    autocomplete_fields = (
        "shipment",
        "changed_by",
    )

    readonly_fields = (
        "shipment",
        "from_status",
        "to_status",
        "changed_by",
        "note",
        "created_at",
    )

@admin.register(DispatchBatch)
class DispatchBatchAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "branch",
        "status",
        "scheduled_at",
        "dispatched_at",
        "delivered_at",
        "approved_at",
        "completed_at",
    )

    list_filter = (
        "branch",
        "status",
    )

    search_fields = (
        "id",
        "branch__name",
    )

    autocomplete_fields = (
        "branch",
    )

@admin.register(DispatchOrder)
class DispatchOrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "batch",
        "order",
        "status",
    )

    list_filter = (
        "batch",
        "status",
    )

    search_fields = (
        "id",
        "batch__id",
        "order__tracking_code",
    )

    autocomplete_fields = (
        "batch",
        "order",
    )

@admin.register(DispatchFreightAssignment)
class DispatchFreightAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "dispatch_order",
        "freight_company",
        "assigned_at",
        "accepted_at",
        "delivered_at",
    )

    list_filter = (
        "freight_company",
    )

    search_fields = (
        "id",
        "dispatch_order__id",
        "dispatch_order__order__tracking_code",
        "freight_company__name",
    )

    autocomplete_fields = (
        "dispatch_order",
        "freight_company",
    )