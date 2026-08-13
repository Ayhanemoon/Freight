from django.core.management.base import BaseCommand
from faker import Faker
import random
from datetime import datetime
from accounts.models import User, Profile
from blog.models import Post, Category

category_list = [
    "technology",
    "information",
    "notes",
    "programming",
    "development",
]


class Command(BaseCommand):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fake = Faker()

    def handle(self, *args, **options):
        user = User.objects.create_user(
            email=self.fake.email(),
            password="test@1234567",
            is_active=True,
            is_verified=True,
        )
        profile = Profile.objects.get(user=user)
        profile.first_name = self.fake.first_name()
        profile.last_name = self.fake.last_name()
        profile.description = self.fake.paragraph(nb_sentences=5)
        profile.save()

        for name in category_list:
            Category.objects.get_or_create(name=name)

        for _ in range(10):
            Post.objects.create(
                author=profile,
                title=self.fake.sentence(nb_words=5),
                content=self.fake.paragraph(nb_sentences=10),
                category=Category.objects.get(name=random.choice(category_list)),
                status=random.choice([True, False]),
                published_at=datetime.now(),
            )
