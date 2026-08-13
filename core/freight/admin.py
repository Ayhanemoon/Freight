from django.contrib import admin

from freight.models import Branch, Customer, FreightCompany


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