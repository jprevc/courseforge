from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import FormView

from progress.models import UserProgress


def home(request: HttpRequest) -> HttpResponse:
    """Landing page; redirects authenticated users to the dashboard."""
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "users/home.html")


def dashboard(request: HttpRequest) -> HttpResponse:
    """Dashboard showing links to My courses and Browse all courses."""
    if not request.user.is_authenticated:
        return redirect("login")

    created_courses = list(request.user.created_courses.prefetch_related("exercises").all())

    # Build a per-course progress map: {course_id: completed_exercise_count}
    course_ids = [c.pk for c in created_courses]
    progress_qs = (
        UserProgress.objects.filter(user=request.user, exercise__course_id__in=course_ids)
        .values("exercise__course_id", "exercise_id")
        .distinct()
    )
    completed_by_course: dict[int, int] = {}
    for row in progress_qs:
        cid = row["exercise__course_id"]
        completed_by_course[cid] = completed_by_course.get(cid, 0) + 1

    courses_with_progress = []
    for course in created_courses:
        total = course.exercises.count()
        completed = completed_by_course.get(course.pk, 0)
        pct = round(completed / total * 100) if total > 0 else 0
        courses_with_progress.append(
            {
                "course": course,
                "total_exercises": total,
                "completed_exercises": completed,
                "progress_pct": pct,
            }
        )

    return render(request, "users/dashboard.html", {"courses_with_progress": courses_with_progress})


class RegisterView(FormView):
    """Registration view: creates user and logs them in on success."""

    form_class = UserCreationForm
    template_name = "users/register.html"
    success_url = reverse_lazy("dashboard")

    def form_valid(self, form: UserCreationForm) -> HttpResponse:
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)


class CustomLoginView(LoginView):
    """Login view using a custom template; redirects already-authenticated users."""

    template_name = "users/login.html"
    redirect_authenticated_user = True


class CustomLogoutView(LogoutView):
    """Logout view; redirects to the home page after logout."""

    next_page = "home"
