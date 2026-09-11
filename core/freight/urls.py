from django.urls import path, include

app_name = "freight"

urlpatterns = [
    path("api/v1/", include("freight.api.v1.urls")),
]