from django.apps import AppConfig


class AgentConfig(AppConfig):
    """AppConfig for the agent package (course generator tests)."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "agent"
    label = "agent"
