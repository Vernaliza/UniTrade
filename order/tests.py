from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from item.models import Category, Item
from .models import Order

User = get_user_model()


class OrderModelTest(TestCase):

    def setUp(self):
        self.customer = User.objects.create_user(
            username="buyer",
            password="123456"
        )

        self.seller = User.objects.create_user(
            username="seller",
            password="123456"
        )

        self.category = Category.objects.create(
            name="Test Electronics Order"
        )

        self.item = Item.objects.create(
            title="Phone",
            price=Decimal("300.00"),
            stock=1,
            category=self.category,
            seller=self.seller
        )

    def test_order_creation(self):
        order = Order.objects.create(
            order_id="ORD001",
            customer=self.customer,
            seller=self.seller,
            item=self.item,
            quantity=1,
            amount=Decimal("300.00"),
            status="pending"
        )

        self.assertEqual(order.order_id, "ORD001")
        self.assertEqual(order.customer.username, "buyer")
        self.assertEqual(order.seller.username, "seller")
        self.assertEqual(order.item.title, "Phone")
        self.assertEqual(order.quantity, 1)
        self.assertEqual(order.amount, Decimal("300.00"))
        self.assertEqual(order.status, "pending")