"""Tests for register and login flows."""

from urllib.parse import urlparse

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class RegisterViewTests(TestCase):
    """Tests for the registration flow."""

    def test_register_get_returns_200(self) -> None:
        """GET register page returns 200."""
        client = Client()
        response = client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/register.html")

    def test_register_post_creates_user_and_redirects(self) -> None:
        """POST with valid data creates user, logs in, and redirects to dashboard."""
        client = Client()
        response = client.post(
            reverse("register"),
            {
                "username": "newuser",
                "password1": "ComplexPass123!",
                "password2": "ComplexPass123!",
            },
        )
        self.assertRedirects(response, reverse("dashboard"))
        self.assertTrue(User.objects.filter(username="newuser").exists())
        user = User.objects.get(username="newuser")
        self.assertTrue(user.check_password("ComplexPass123!"))
        # Session should have user logged in; dashboard should be accessible
        dashboard_response = client.get(reverse("dashboard"))
        self.assertEqual(dashboard_response.status_code, 200)

    def test_register_post_invalid_data_returns_form_errors(self) -> None:
        """POST with invalid data (e.g. password mismatch) re-renders form with errors."""
        client = Client()
        response = client.post(
            reverse("register"),
            {
                "username": "newuser",
                "password1": "ComplexPass123!",
                "password2": "DifferentPass123!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="newuser").exists())
        self.assertContains(response, "password", status_code=200)


class LoginViewTests(TestCase):
    """Tests for the login flow."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(username="testuser", password="testpass123")

    def test_login_get_returns_200(self) -> None:
        """GET login page returns 200."""
        client = Client()
        response = client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/login.html")

    def test_login_post_valid_credentials_redirects(self) -> None:
        """POST with valid credentials logs in and redirects."""
        client = Client()
        response = client.post(
            reverse("login"),
            {"username": "testuser", "password": "testpass123"},
        )
        self.assertEqual(response.status_code, 302)
        # Session should have user logged in
        dashboard_response = client.get(reverse("dashboard"))
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertEqual(dashboard_response.wsgi_request.user.username, "testuser")

    def test_login_post_invalid_credentials_returns_form_errors(self) -> None:
        """POST with wrong password re-renders login form; user is not logged in."""
        client = Client()
        response = client.post(
            reverse("login"),
            {"username": "testuser", "password": "wrongpassword"},
        )
        self.assertEqual(response.status_code, 200)
        # Still on login page (not redirected); unauthenticated user cannot access dashboard
        dashboard_response = client.get(reverse("dashboard"))
        self.assertEqual(dashboard_response.status_code, 302)
        location = dashboard_response.get("Location", "")
        self.assertEqual(urlparse(location).path, reverse("login"))

    def test_login_redirect_authenticated_user(self) -> None:
        """Authenticated user visiting login is redirected (redirect_authenticated_user)."""
        client = Client()
        client.force_login(self.user)
        response = client.get(reverse("login"))
        self.assertEqual(response.status_code, 302)
