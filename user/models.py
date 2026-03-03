from django.db import models

# Create your models here.
from django.contrib.auth.models import User

class Profile(models.Model):
    # Link to the built-in User model
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Role selection to distinguish between Students and Merchants
    class Role(models.TextChoices):
        STUDENT = 'student', 'Student/Buyer'
        MERCHANT = 'merchant', 'Merchant/Seller'
    
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.STUDENT
    )
    
    # Fields required by your ER Diagram [cite: 101, 111, 121]
    student_id = models.CharField(max_length=20, blank=True, verbose_name="Student ID")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Phone Number")
    address = models.CharField(max_length=255, blank=True, verbose_name="Address")

    def __str__(self):
        return f"{self.user.username}'s {self.role} Profile"