from django.db import models


class Customer(models.Model):
    """Customer model for storing customer information"""
    name = models.CharField(max_length=200, verbose_name="Name")
    email = models.EmailField(verbose_name="Email")
    registration_date = models.DateField(verbose_name="Registration Date")
    
    class Meta:
        verbose_name = "Customer"
        verbose_name_plural = "Customers"
        ordering = ['-registration_date']
    
    def __str__(self):
        return self.name


class Product(models.Model):
    """Product model for storing product information"""
    name = models.CharField(max_length=200, verbose_name="Name")
    category = models.CharField(max_length=100, verbose_name="Category")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Price")
    
    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Order(models.Model):
    """Order model linking customers and products"""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="Customer")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Product")
    order_date = models.DateField(verbose_name="Order Date")
    quantity = models.IntegerField(verbose_name="Quantity")
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        default='pending',
        verbose_name="Status"
    )
    
    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ['-order_date']
    
    def __str__(self):
        return f"Order {self.id} - {self.customer.name} - {self.product.name}"
