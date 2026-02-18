from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import FormView


def home(request: HttpRequest) -> HttpResponse:
    """Landing page; redirects authenticated users to the dashboard."""
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "users/home.html")


def dashboard(request: HttpRequest) -> HttpResponse:
    """Dashboard showing links to My courses and Browse all courses."""
    if not request.user.is_authenticated:
        return redirect("login")
    return render(request, "users/dashboard.html")


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
