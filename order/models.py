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
    quantity = models.PositiveIntegerField(default=1, verbose_name='Quantity')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Dealt Price', default=Decimal('0.00'))
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending', verbose_name='Order Status')
    created_time = models.DateTimeField(auto_now_add=True, verbose_name='Order Created Time')
    paid_time = models.DateTimeField(null=True, blank=True, verbose_name='Order Paid Time')


class Basket(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="basket")
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    def total_amount(self) -> Decimal:
        return sum((bi.subtotal() for bi in self.items.all()), Decimal("0.00"))

    def __str__(self):
        return f"Basket<{self.user_id}>"


class BasketItem(models.Model):
    basket = models.ForeignKey(Basket, on_delete=models.CASCADE, related_name="items")
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    # You can choose to update to the latest price every time you make an additional purchase, or maintain the first purchase price
    # During settlement, the price is usually frozen again to prevent price changes midway
    #可以选择每次加购时更新成最新价，或者保持第一次加购价
    #结算时通常还会再“冻结价格”一次，防止中途改价
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    #When the user repeatedly clicks "Add to Basket", the quantity+=1 is added instead of adding a new line
    #用户重复点“加入购物车”时，就把 quantity += 1，而不是新增一行
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["basket", "item"], name="uniq_basket_item")
        ]

    def subtotal(self) -> Decimal:
        return (self.unit_price or Decimal("0.00")) * self.quantity

    def __str__(self):
        return f"BasketItem<{self.basket_id}:{self.item_id} x {self.quantity}>"