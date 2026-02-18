from django.contrib import admin

from .models import UserProgress


@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    """Admin for UserProgress: list by user, exercise, correct, date; filter by correct."""

    list_display = ("user", "exercise", "correct", "completed_at")
    list_filter = ("correct",)
