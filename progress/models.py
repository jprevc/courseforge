from django.conf import settings
from django.db import models

from courses.models import Exercise


class UserProgress(models.Model):
    """One recorded attempt: user answered an exercise (correct or incorrect) at a given time."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="exercise_progress",
    )
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name="user_progress",
    )
    completed_at = models.DateTimeField(auto_now_add=True)
    correct = models.BooleanField()

    class Meta:
        ordering = ["-completed_at"]

    def __str__(self) -> str:
        return f"{self.user} – {self.exercise} ({'correct' if self.correct else 'wrong'})"
