from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.utils.text import slugify


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
        SOLD = "sold", "Sold"
        DELISTED = "delisted", "Delisted"
        HIDDEN = "hidden", "Hidden"
        DELETED = "deleted", "Deleted"



    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)], )
    stock = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)], )
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="items", )
    seller = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="items", )
    image = models.ImageField(upload_to=item_image_path, blank=True, null=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE, db_index=True, )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title