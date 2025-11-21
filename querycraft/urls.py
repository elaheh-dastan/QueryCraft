from django.urls import path

from . import views

app_name = "querycraft"

urlpatterns = [
    path("", views.query_form, name="query_form"),
    path("api/query/", views.process_query, name="process_query"),
]
