from django.contrib import admin

from .models import Course, Exercise


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "created_by", "created_at")


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ("course", "order_index", "exercise_type", "question")
    list_filter = ("exercise_type",)
