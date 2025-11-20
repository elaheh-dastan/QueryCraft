from django.contrib import admin

from .models import Customer, Order, Product


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "email", "registration_date"]
    list_filter = ["registration_date"]
    search_fields = ["name", "email"]
    date_hierarchy = "registration_date"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "category", "price"]
    list_filter = ["category"]
    search_fields = ["name", "category"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "customer", "product", "order_date", "quantity", "status"]
    list_filter = ["status", "order_date"]
    search_fields = ["customer__name", "product__name"]
    date_hierarchy = "order_date"
    raw_id_fields = ["customer", "product"]
