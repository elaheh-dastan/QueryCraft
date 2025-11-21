from django.urls import path

from . import views

app_name = "querycraft"

urlpatterns = [
    path("", views.query_form, name="query_form"),
    path("api-client/", views.api_client, name="api_client"),  # Simple API client page
    path("api/query/", views.process_query, name="process_query"),
]
