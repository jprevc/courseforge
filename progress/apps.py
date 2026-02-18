"""Progress app: UserProgress model for exercise attempts."""

from django.apps import AppConfig


class ProgressConfig(AppConfig):
    """AppConfig for the progress app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "progress"
