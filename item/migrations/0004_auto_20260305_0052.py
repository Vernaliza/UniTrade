from django.db import migrations
from django.utils.text import slugify  # NEW: Import slugify

def create_default_categories(apps, schema_editor):
    Category = apps.get_model('item', 'Category')
    
    default_categories = [
        "Textbooks",
        "Electronics",
        "Clothing",
        "Furniture",
        "Kitchen & Dorm",
        "Outdoor & Hiking Gear",
        "Fitness & Home Workout",
        "Stationery & Study",
        "Bikes & Scooters",
        "Miscellaneous"
    ]
    
    for name in default_categories:
        Category.objects.get_or_create(
            name=name, 
            defaults={'slug': slugify(name)}
        )

class Migration(migrations.Migration):
    
    dependencies = [
        # (Leave whatever Django put here)
        ('item', '0003_item_condition'),
    ]

    operations = [
        migrations.RunPython(create_default_categories),
    ]