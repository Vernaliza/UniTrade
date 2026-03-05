from django import forms
from django.core.exceptions import ValidationError

from .models import Item


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ["title", "category", "price", "stock","condition","description", "image"]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter item title", "autofocus": True}
            ),
            "category": forms.Select(attrs={"class": "form-select"}),
            "price": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "Enter item price", "min": "0", "step": "0.01"}
            ),
            "condition": forms.Select(attrs={"class": "form-control"}),
            "description": forms.Textarea(
                attrs={"class": "form-control", "placeholder": "Describe condition, usage, and any defects", "rows": 5}
            ),
            "image": forms.ClearableFileInput(attrs={"class": "form-control", "accept": "image/*"}),
            "stock": forms.NumberInput(attrs={"class": "form-control", "min": "1", "value": "1"}),
        }

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if not image:
            return image

        max_size_mb = 5
        if image.size > max_size_mb * 1024 * 1024:
            raise ValidationError(f"Image size must be under {max_size_mb}MB.")

        content_type = getattr(image, "content_type", "")
        if content_type and not content_type.startswith("image/"):
            raise ValidationError("Uploaded file must be an image.")
        return image