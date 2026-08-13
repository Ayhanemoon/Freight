from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Profile

# Register your models here.


class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ("mobile", "is_staff", "is_active", "is_mobile_verified")
    list_filter = ("mobile", "is_staff", "is_active", "is_mobile_verified")
    fieldsets = (
        ("Authentication", {"fields": ("mobile", "password")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_staff",
                    "is_active",
                    "is_mobile_verified",
                    "is_superuser",
                )
            },
        ),
        ("Group Permissions", {"fields": ("groups", "user_permissions")}),
        ("Important Date", {"fields": ("last_login",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "mobile",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                    "is_mobile_verified",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
    )
    search_fields = ("mobile",)
    ordering = ("mobile",)


admin.site.register(Profile)
admin.site.register(User, CustomUserAdmin)
