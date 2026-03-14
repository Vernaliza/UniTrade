from allauth.account.adapter import DefaultAccountAdapter
from django.core.exceptions import ValidationError
from django.urls import reverse


class AcUkAccountAdapter(DefaultAccountAdapter):
    allowed_domain_suffix = ".ac.uk"

    def clean_email(self, email):
        email = super().clean_email(email).strip().lower()
        if not email.endswith(self.allowed_domain_suffix):
            raise ValidationError("Please use an academic email ending with .ac.uk.")
        return email

    def get_login_redirect_url(self, request):
        return reverse('user:dashboard')

    def get_logout_redirect_url(self, request):
        return reverse('index')

    def get_email_verification_redirect_url(self, email_address):
        return reverse('user:dashboard')