from django.db import models
from django.urls import reverse

# Create your models here.


class Post(models.Model):
    """Model representing a blog post."""

    author = models.ForeignKey("accounts.Profile", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="blog_images/", null=True, blank=True)
    title = models.CharField(max_length=250, blank=False)
    content = models.TextField()
    status = models.BooleanField(default=True)
    category = models.ForeignKey(
        "Category", on_delete=models.SET_NULL, null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title

    def get_snippet(self):
        """Returns a snippet of the content."""
        return self.content[:25] + "..."

    def get_absolute_api_url(self):
        """Returns the absolute URL for the post."""
        return reverse("blog:api-v1:post-detail", args=[str(self.id)])


class Category(models.Model):
    """Model representing a blog post category."""

    name = models.CharField(max_length=250)

    def __str__(self):
        return self.name
