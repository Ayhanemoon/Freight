from django.views.generic.base import TemplateView
from .models import Post

# Create your views here


class PostListView(TemplateView):
    """Class-based view for the blog index page."""

    template_name = "blog/index.html"

    def get_context_data(self, **kwargs):
        """Add extra context to the template."""
        context = super().get_context_data(**kwargs)
        context["posts"] = Post.objects.all().order_by("-published_at")
        return context


class DetailView(TemplateView):
    """Class-based view for the blog detail page."""

    template_name = "blog/detail.html"

    def get_context_data(self, **kwargs):
        """Add extra context to the template."""
        context = super().get_context_data(**kwargs)
        pk = self.kwargs.get("pk")
        context["post"] = Post.objects.get(pk=pk)
        return context
