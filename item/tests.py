from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Category, Item


class ItemModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="seller",
            password="123456"
        )
        self.category = Category.objects.create(
            name="Category A"
        )

    def test_category_slug_is_generated(self):
        category = Category.objects.create(name="Mobile Phones")
        self.assertEqual(category.slug, "mobile-phones")

    def test_item_price_validation(self):
        item = Item(
            title="Invalid Item",
            price=0,
            category=self.category,
            seller=self.user
        )

        with self.assertRaises(ValidationError):
            item.full_clean()