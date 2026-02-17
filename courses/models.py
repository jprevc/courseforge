from django.db import models
from django.conf import settings


class Course(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, allow_unicode=True)
    overview = models.TextField()
    cheatsheet = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_courses",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    topic_normalized = models.CharField(max_length=255, blank=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Exercise(models.Model):
    class ExerciseType(models.TextChoices):
        MULTIPLE_CHOICE = "multiple_choice", "Multiple choice"
        MATCHING_PAIRS = "matching_pairs", "Matching pairs"

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="exercises"
    )
    order_index = models.PositiveIntegerField(default=0)
    exercise_type = models.CharField(
        max_length=20, choices=ExerciseType.choices
    )
    question = models.TextField()
    payload = models.JSONField(
        help_text="multiple_choice: {options: [...], correct_index: int}; matching: {pairs: [{left, right}, ...]}"
    )

    class Meta:
        ordering = ["course", "order_index"]
        unique_together = [("course", "order_index")]

    def __str__(self):
        return f"{self.course.title} – #{self.order_index} ({self.exercise_type})"
