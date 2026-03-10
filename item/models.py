from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.text import slugify
from decimal import Decimal


class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


def item_image_path(instance, filename):
    ts = int(timezone.now().timestamp())
    seller_id = instance.seller_id or "unknown"
    return f"items/{seller_id}/{ts}_{filename}"


class Item(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PENDING = "pending", "Pending"   # <--- NEW: Added Pending state
        SOLD = "sold", "Sold"
        DELISTED = "delisted", "Delisted"
        HIDDEN = "hidden", "Hidden"
        DELETED = "deleted", "Deleted"

    class Condition(models.TextChoices):
        NEW = "new", "Brand New"
        LIKE_NEW = "like_new", "Like New / Open Box"
        GOOD = "good", "Good / Used"
        FAIR = "fair", "Fair / Acceptable"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], ) # fix price min limit
    stock = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(999)])
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="items", )
    seller = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="items", )
    image = models.ImageField(upload_to=item_image_path, blank=True, null=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE, db_index=True, )
    condition = models.CharField(max_length=20, choices=Condition.choices, default=Condition.GOOD)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    rating_sum = models.PositiveIntegerField(default=0)
    rating_count = models.PositiveIntegerField(default=0)
    rating_avg = models.DecimalField(max_digits=3, decimal_places=2, default=0)

    def __str__(self):
        return self.title