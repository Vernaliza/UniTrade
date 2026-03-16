from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model

from item.models import Category, Item
from order.models import Order
from .models import Review

User = get_user_model()


class ReviewModelTest(TestCase):

    def setUp(self):
        self.customer = User.objects.create_user(
            username="buyer2",
            password="123456"
        )

        self.seller = User.objects.create_user(
            username="seller2",
            password="123456"
        )

        self.category, _ = Category.objects.get_or_create(
            name="TestElectronicsReview"
        )

        self.item = Item.objects.create(
            title="Laptop",
            price=Decimal("500.00"),
            stock=1,
            category=self.category,
            seller=self.seller
        )

        self.order = Order.objects.create(
            order_id="ORD002",
            customer=self.customer,
            seller=self.seller,
            item=self.item,
            quantity=1,
            amount=Decimal("500.00"),
            status="completed"
        )

    def test_review_creation(self):
        review = Review.objects.create(
            customer=self.customer,
            order=self.order,
            rating=5,
            content="Great product"
        )

        self.assertEqual(review.customer.username, "buyer2")
        self.assertEqual(review.order.order_id, "ORD002")
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.content, "Great product")