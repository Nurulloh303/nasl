from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.accounts.models import Profile

User = get_user_model()


class AuthenticationTests(TestCase):
    """Authentication va registration tests."""

    def setUp(self):
        self.client = APIClient()
        self.register_url = "/api/auth/register/"
        self.login_url = "/api/auth/login/"
        self.me_url = "/api/auth/me/"

    def test_user_registration(self):
        """Test user registration."""
        data = {
            "username": "testuser",
            "password": "testpass123",
            "password2": "testpass123",
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_duplicate_username(self):
        """Test duplicate username registration."""
        User.objects.create_user(username="existing", password="pass123")
        data = {
            "username": "existing",
            "password": "testpass123",
            "password2": "testpass123",
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_mismatch(self):
        """Test password mismatch on registration."""
        data = {
            "username": "testuser",
            "password": "testpass123",
            "password2": "different123",
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_login(self):
        """Test user login."""
        User.objects.create_user(username="testuser", password="testpass123")
        data = {
            "username": "testuser",
            "password": "testpass123",
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_invalid_credentials(self):
        """Test login with invalid credentials."""
        User.objects.create_user(username="testuser", password="testpass123")
        data = {
            "username": "testuser",
            "password": "wrongpassword",
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_me_endpoint_authenticated(self):
        """Test /me endpoint with authentication."""
        user = User.objects.create_user(username="testuser", password="testpass123")
        self.client.force_authenticate(user=user)
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_me_endpoint_unauthenticated(self):
        """Test /me endpoint without authentication."""
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
