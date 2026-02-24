import uuid

from django.conf import settings
from django.db import models


class Course(models.Model):
    """A course: title, overview, cheatsheet, and a list of exercises. Created by a user."""

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, allow_unicode=True)
    overview = models.TextField()
    cheatsheet = models.TextField()
    has_questions = models.BooleanField(default=True)
    has_flashcards = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_courses",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    topic_normalized = models.CharField(max_length=255, blank=True, db_index=True)
    generation_model = models.CharField(
        max_length=128,
        blank=True,
        default="",
        help_text="LLM model used to generate this course (e.g. openai:gpt-5-mini). Empty for courses created before this was tracked.",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title


class CourseGenerationJob(models.Model):
    """Tracks an async course generation; status is polled by the generating page."""

    class Status(models.TextChoices):
        PENDING = "pending"
        RUNNING = "running"
        COMPLETE = "complete"
        FAILED = "failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    status_message = models.CharField(max_length=255, blank=True)
    course = models.ForeignKey(Course, null=True, blank=True, on_delete=models.SET_NULL, related_name="generation_jobs")
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generation_jobs",
    )
    topic = models.CharField(max_length=255, blank=True)

    def __str__(self) -> str:
        return f"Job {self.id} ({self.status})"


class Exercise(models.Model):
    """A single exercise (multiple choice or matching pairs) belonging to a course."""

    class ExerciseType(models.TextChoices):
        MULTIPLE_CHOICE = "multiple_choice", "Multiple choice"
        MATCHING_PAIRS = "matching_pairs", "Matching pairs"

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="exercises")
    order_index = models.PositiveIntegerField(default=0)
    exercise_type = models.CharField(max_length=20, choices=ExerciseType.choices)
    question = models.TextField()
    payload = models.JSONField(
        help_text="multiple_choice: {options: [...], correct_index: int}; matching: {pairs: [{left, right}, ...]}"
    )

    class Meta:
        ordering = ["course", "order_index"]
        unique_together = [("course", "order_index")]

    def __str__(self) -> str:
        return f"{self.course.title} – #{self.order_index} ({self.exercise_type})"


class Flashcard(models.Model):
    """A single flashcard belonging to a course."""

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="flashcards")
    order_index = models.PositiveIntegerField(default=0)
    front = models.TextField()
    back = models.TextField()

    class Meta:
        ordering = ["course", "order_index"]
        unique_together = [("course", "order_index")]

    def __str__(self) -> str:
        return f"{self.course.title} – flashcard #{self.order_index}"


class Notification(models.Model):
    """A notification for a user, optionally linked to a course."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    message = models.CharField(max_length=500)
    course = models.ForeignKey(Course, null=True, blank=True, on_delete=models.SET_NULL, related_name="notifications")
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Notification({self.user_id}): {self.message[:50]}"
