"""
URL configuration for QueryCraft project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('querycraft.urls')),  # Include QueryCraft app URLs
]

