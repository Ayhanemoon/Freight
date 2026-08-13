from rest_framework import serializers
from blog.models import Post, Category
from accounts.models import Profile


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for blog category data."""

    class Meta:
        model = Category
        fields = ["id", "name"]


class PostSerializer(serializers.ModelSerializer):
    """Serializer for blog post data."""

    snippet = serializers.ReadOnlyField(source="get_snippet")
    relative_url = serializers.URLField(source="get_absolute_api_url", read_only=True)
    absolute_url = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id",
            "author",
            "image",
            "title",
            "content",
            "snippet",
            "status",
            "category",
            "relative_url",
            "absolute_url",
            "created_at",
            "updated_at",
            "published_at",
        ]
        read_only_fields = ["author"]

    def get_absolute_url(self, obj):
        request = self.context.get("request")
        if request is not None:
            return request.build_absolute_uri(obj.get_absolute_api_url())
        return obj.get_absolute_api_url()

    def to_representation(self, instance):
        request = self.context.get("request")
        representation = super().to_representation(instance)
        if request.parser_context.get("view").action == "list":
            representation.pop("content", None)
        else:
            representation.pop("snippet", None)
            representation.pop("relative_url", None)
            representation.pop("absolute_url", None)
        representation["category"] = CategorySerializer(
            instance.category, context={"request": request}
        ).data
        # Customize the representation if needed
        return representation

    def create(self, validated_data):
        validated_data["author"] = Profile.objects.get(
            user__id=self.context["request"].user.id
        )
        return Post.objects.create(**validated_data)
