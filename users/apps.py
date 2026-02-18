"""Users app: auth, registration, dashboard."""

from django.apps import AppConfig


class UsersConfig(AppConfig):
    """AppConfig for the users app (auth and profile)."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "users"
