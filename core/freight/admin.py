from django.contrib import admin

from freight.models import (
    Branch,
    Customer,
    FreightCompany,
    ShipmentOrder,
    Parcel,
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