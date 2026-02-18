"""Views for course listing, creation, detail, and exercise flow."""

import random
from typing import Any

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify

from agent.run_course_gen import run_course_generator_sync
from progress.models import UserProgress

from .forms import CreateCourseForm
from .models import Course, Exercise


def course_list(request: HttpRequest) -> HttpResponse:
    """List all courses (browse)."""
    courses = Course.objects.all().order_by("-created_at")
    return render(request, "courses/course_list.html", {"courses": courses})


@login_required
def course_create(request: HttpRequest) -> HttpResponse:
    """Create a new course: show form (GET) or run agent and save (POST)."""
    if request.method != "POST":
        form = CreateCourseForm()
        return render(request, "courses/course_create.html", {"form": form})
    form = CreateCourseForm(request.POST)
    if not form.is_valid():
        return render(request, "courses/course_create.html", {"form": form})
    topic = form.cleaned_data["topic"].strip()
    if not topic:
        form.add_error("topic", "Topic is required.")
        return render(request, "courses/course_create.html", {"form": form})
    try:
        content = run_course_generator_sync(topic)
    except Exception as e:
        messages.error(
            request,
            f"Failed to generate course: {e}. Check your API key and try again.",
        )
        return render(request, "courses/course_create.html", {"form": form})
    base_slug = slugify(content.title, allow_unicode=True) or "course"
    slug = base_slug
    n = 1
    while Course.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{n}"
        n += 1
    course = Course.objects.create(
        title=content.title,
        slug=slug,
        overview=content.overview,
        cheatsheet=content.cheatsheet,
        created_by=request.user,
        topic_normalized=topic.lower()[:255],
    )
    for i, item in enumerate(content.exercises):
        if item.type == "multiple_choice" and item.multiple_choice:
            mc = item.multiple_choice
            Exercise.objects.create(
                course=course,
                order_index=i,
                exercise_type=Exercise.ExerciseType.MULTIPLE_CHOICE,
                question=mc.question,
                payload={
                    "options": mc.options,
                    "correct_index": mc.correct_index,
                },
            )
        elif item.type == "matching" and item.matching:
            mat = item.matching
            Exercise.objects.create(
                course=course,
                order_index=i,
                exercise_type=Exercise.ExerciseType.MATCHING_PAIRS,
                question=mat.question,
                payload={
                    "pairs": [{"left": p.left, "right": p.right} for p in mat.pairs],
                },
            )
    messages.success(request, f"Course “{course.title}” created.")
    return redirect("courses:detail", slug=course.slug)


def course_detail(request: HttpRequest, slug: str) -> HttpResponse:
    """Show course overview, cheatsheet, exercise count, and progress (X/Y) for the current user."""
    course = get_object_or_404(Course, slug=slug)
    exercises = list(course.exercises.order_by("order_index"))
    completed_count = 0
    if request.user.is_authenticated and exercises:
        completed_count = (
            UserProgress.objects.filter(
                user=request.user,
                exercise__course=course,
            )
            .values("exercise")
            .distinct()
            .count()
        )
    return render(
        request,
        "courses/course_detail.html",
        {
            "course": course,
            "exercises": exercises,
            "completed_count": completed_count,
            "total_exercises": len(exercises),
        },
    )


@login_required
def course_start(request: HttpRequest, slug: str) -> HttpResponse:
    """Redirect to the first exercise or back to course detail if there are no exercises."""
    course = get_object_or_404(Course, slug=slug)
    first = course.exercises.order_by("order_index").first()
    if not first:
        return redirect("courses:detail", slug=slug)
    return redirect("courses:exercise", slug=slug, index=0)


def _check_multiple_choice(exercise: Exercise, selected_index: Any) -> bool:
    """Return True if the selected option index matches the correct answer."""
    try:
        idx = int(selected_index)
        return 0 <= idx < len(exercise.payload.get("options", [])) and idx == exercise.payload.get("correct_index")
    except (TypeError, ValueError):
        return False


def _check_matching(exercise: Exercise, selected_by_left: dict[int, Any]) -> bool:
    """Return True if each left item is matched to the correct right item (by original index)."""
    pairs = exercise.payload.get("pairs", [])
    if len(selected_by_left) != len(pairs):
        return False
    for i in range(len(pairs)):
        try:
            if int(selected_by_left.get(i)) != i:
                return False
        except (TypeError, ValueError):
            return False
    return True


@login_required
def exercise_view(request: HttpRequest, slug: str, index: int) -> HttpResponse:
    """Show one exercise (GET) or validate answer and redirect to next / complete (POST)."""
    course = get_object_or_404(Course, slug=slug)
    exercises = list(course.exercises.order_by("order_index"))
    if index < 0 or index >= len(exercises):
        return redirect("courses:detail", slug=slug)
    exercise = exercises[index]

    if request.method == "POST":
        correct = False
        if exercise.exercise_type == Exercise.ExerciseType.MULTIPLE_CHOICE:
            correct = _check_multiple_choice(exercise, request.POST.get("answer"))
        elif exercise.exercise_type == Exercise.ExerciseType.MATCHING_PAIRS:
            selected = {i: request.POST.get(f"match_{i}") for i in range(len(exercise.payload.get("pairs", [])))}
            correct = _check_matching(exercise, selected)
        UserProgress.objects.create(
            user=request.user,
            exercise=exercise,
            correct=correct,
        )
        next_index = index + 1
        if next_index >= len(exercises):
            messages.success(request, "Course complete! Well done.")
            return redirect("courses:detail", slug=slug)
        messages.success(request, "Correct!" if correct else "Not quite. You can try again on the next exercise.")
        return redirect("courses:exercise", slug=slug, index=next_index)

    # GET: prepare context for template
    context = {
        "course": course,
        "exercise": exercise,
        "index": index,
        "total": len(exercises),
    }
    if exercise.exercise_type == Exercise.ExerciseType.MATCHING_PAIRS:
        pairs = exercise.payload.get("pairs", [])
        right_indices = list(range(len(pairs)))
        random.shuffle(right_indices)
        context["left_items"] = [p["left"] for p in pairs]
        # Options for each dropdown: (original_index, display_text) in shuffled order
        context["right_options"] = [(right_indices[k], pairs[right_indices[k]]["right"]) for k in range(len(pairs))]
    return render(request, "courses/exercise.html", context)
