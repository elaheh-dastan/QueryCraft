from django.db import models
from django.utils import timezone
from datetime import timedelta


class User(models.Model):
    """User model for storing user information"""
    username = models.CharField(max_length=100, unique=True, verbose_name="Username")
    email = models.EmailField(verbose_name="Email")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Registration Date")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.username


class Order(models.Model):
    """Order model for additional sample data"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="User")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total Amount")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Order Date")
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
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order {self.id} - {self.user.username}"

