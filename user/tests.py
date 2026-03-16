from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse


class AuthViewTest(TestCase):

    def test_login_required_redirect(self):
        response = self.client.get(reverse("user:profile"))
        self.assertEqual(response.status_code, 302)

    def test_logged_in_user_access_profile(self):
        user = User.objects.create_user(
            username="testuser",
            password="123456"
        )

        self.client.login(username="testuser", password="123456")
        response = self.client.get(reverse("user:profile"))

        self.assertEqual(response.status_code, 200)
