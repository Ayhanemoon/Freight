from django_filters import rest_framework as filters
from blog.models import Post


class PostFilter(filters.FilterSet):
    """Filter class for blog posts."""

    class Meta:
        model = Post
        fields = {
            "author": ["exact"],
            "category": ["exact", "in"],
            "status": ["exact"],
        }
