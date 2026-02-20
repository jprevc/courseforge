"""Views for course listing, creation, detail, and exercise flow."""

import random
import threading
from typing import Any

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import close_old_connections
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.text import slugify

from agent.run_course_gen import run_course_generator_sync
from progress.models import UserProgress

from .forms import CreateCourseForm
from .models import Course, CourseGenerationJob, Exercise


def _run_generation(
    job_id: str,
    topic: str,
    user_id: int,
    difficulty: str = "beginner",
    additional_instructions: str | None = None,
    num_exercises: int | None = None,
) -> None:
    """Background thread: run course generator and update job (status, course, error)."""
    try:
        close_old_connections()
        job = CourseGenerationJob.objects.get(pk=job_id)
        user = get_user_model().objects.get(pk=user_id)

        job.status = CourseGenerationJob.Status.RUNNING
        job.status_message = "Connecting to AI..."
        job.save(update_fields=["status", "status_message"])

        job.status_message = "Generating course outline..."
        job.save(update_fields=["status_message"])

        content = run_course_generator_sync(
            topic=topic,
            difficulty=difficulty,
            additional_instructions=additional_instructions,
            num_exercises=num_exercises,
        )

        job.status_message = "Creating exercises..."
        job.save(update_fields=["status_message"])

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
            created_by=user,
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
                        "explanation": mc.explanation,
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

        job.course = course
        job.status = CourseGenerationJob.Status.COMPLETE
        job.status_message = "Done!"
        job.save(update_fields=["course", "status", "status_message"])
    except Exception as e:
        try:
            close_old_connections()
            job = CourseGenerationJob.objects.get(pk=job_id)
            job.status = CourseGenerationJob.Status.FAILED
            job.error = str(e)
            job.status_message = "Failed"
            job.save(update_fields=["status", "error", "status_message"])
        finally:
            close_old_connections()
    finally:
        close_old_connections()


def course_list(request: HttpRequest) -> HttpResponse:
    """List all courses (browse)."""
    courses = Course.objects.all().order_by("-created_at")
    return render(request, "courses/course_list.html", {"courses": courses})


@login_required
def course_create(request: HttpRequest) -> HttpResponse:
    """Create a new course: show form (GET) or create job, start background thread, redirect (POST)."""
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
    job = CourseGenerationJob.objects.create(status=CourseGenerationJob.Status.PENDING)
    thread = threading.Thread(
        target=_run_generation,
        args=(
            str(job.id),
            topic,
            request.user.id,
            form.cleaned_data["difficulty"],
            form.cleaned_data.get("additional_instructions") or None,
            form.cleaned_data.get("num_exercises"),
        ),
        daemon=True,
    )
    thread.start()
    return redirect("courses:generating", job_id=job.id)


@login_required
def generating_view(request: HttpRequest, job_id: str) -> HttpResponse:
    """Show the generating progress page; JS polls job_status_api until complete."""
    job = get_object_or_404(CourseGenerationJob, pk=job_id)
    return render(request, "courses/generating.html", {"job": job})


@login_required
def job_status_api(request: HttpRequest, job_id: str) -> HttpResponse:
    """Return JSON {status, message, course_slug} for polling."""
    job = get_object_or_404(CourseGenerationJob, pk=job_id)
    data = {
        "status": job.status,
        "message": job.status_message or "",
        "course_slug": job.course.slug if job.course_id else None,
        "error": job.error or "",
    }
    return JsonResponse(data)


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
        selected_answer = None
        matching_result = None
        if exercise.exercise_type == Exercise.ExerciseType.MULTIPLE_CHOICE:
            selected_answer = request.POST.get("answer")
            correct = _check_multiple_choice(exercise, selected_answer)
        elif exercise.exercise_type == Exercise.ExerciseType.MATCHING_PAIRS:
            pairs = exercise.payload.get("pairs", [])
            selected = {i: request.POST.get(f"match_{i}") for i in range(len(pairs))}
            correct = _check_matching(exercise, selected)
            # Build read-only result for template: list of {left, correct_right, user_right}
            matching_result = []
            for i in range(len(pairs)):
                try:
                    user_idx = int(selected.get(i)) if selected.get(i) else None
                except (TypeError, ValueError):
                    user_idx = None
                matching_result.append({
                    "left": pairs[i]["left"],
                    "correct_right": pairs[i]["right"],
                    "user_right": pairs[user_idx]["right"] if user_idx is not None and 0 <= user_idx < len(pairs) else "—",
                    "is_correct": user_idx == i,
                })
        UserProgress.objects.create(
            user=request.user,
            exercise=exercise,
            correct=correct,
        )
        # Render same page with feedback below answers (no redirect)
        context = {
            "course": course,
            "exercise": exercise,
            "index": index,
            "total": len(exercises),
            "answered": True,
            "correct": correct,
            "explanation": exercise.payload.get("explanation", ""),
            "selected_answer": int(selected_answer) if selected_answer not in (None, "") else None,
            "matching_result": matching_result,
        }
        return render(request, "courses/exercise.html", context)

    # GET: prepare context for template (first view of exercise)
    context = {
        "course": course,
        "exercise": exercise,
        "index": index,
        "total": len(exercises),
        "answered": False,
        "correct": None,
        "explanation": "",
        "selected_answer": None,
        "matching_result": None,
    }
    if exercise.exercise_type == Exercise.ExerciseType.MATCHING_PAIRS:
        pairs = exercise.payload.get("pairs", [])
        right_indices = list(range(len(pairs)))
        random.shuffle(right_indices)
        context["left_items"] = [p["left"] for p in pairs]
        context["right_options"] = [(right_indices[k], pairs[right_indices[k]]["right"]) for k in range(len(pairs))]
    return render(request, "courses/exercise.html", context)
