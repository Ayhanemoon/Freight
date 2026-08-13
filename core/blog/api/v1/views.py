from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .serializers import PostSerializer, CategorySerializer
from blog.models import Post, Category
from rest_framework import viewsets
from .permissions import IsOwnerOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .paginations import DefaultPagination
from .filters import PostFilter


class PostModelViewSet(viewsets.ModelViewSet):
    """ViewSet for managing blog posts."""

    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    serializer_class = PostSerializer
    queryset = Post.objects.all().order_by("-published_at")
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = PostFilter
    search_fields = ["title", "content"]
    ordering_fields = ["published_at", "created_at"]
    pagination_class = DefaultPagination


class CategoryModelViewSet(viewsets.ModelViewSet):
    """ViewSet for managing blog categories."""

    permission_classes = [IsAuthenticatedOrReadOnly]
    # Assuming CategorySerializer and Category model exist
    serializer_class = CategorySerializer
    queryset = Category.objects.all().order_by("name")
