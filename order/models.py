from decimal import Decimal

from django.db import models
from django.contrib.auth.models import User
from item.models import Item


class Order(models.Model):
    ORDER_STATUS = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    order_id = models.CharField(max_length=20, unique=True, verbose_name='Order Number')
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders_as_buyer', verbose_name='Buyer')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders_as_seller', verbose_name='Seller')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name='Item')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Dealt Price', default=Decimal('0.00'))
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='Pending', verbose_name='Order Status')
    created_time = models.DateTimeField(auto_now_add=True, verbose_name='Order Created Time')
    paid_time = models.DateTimeField(null=True, blank=True, verbose_name='Order Paid Time')