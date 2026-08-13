from django.contrib import admin
from .models import Post, Category

# Register your models here.


class PostAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "author",
        "status",
        "category",
        "created_at",
        "published_at",
    )
    list_filter = ("status", "category", "author")
    search_fields = ("title", "content")
    prepopulated_fields = {"title": ("title",)}


admin.site.register(Category)
admin.site.register(Post, PostAdmin)
