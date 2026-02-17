from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import FormView


def home(request):
    """Landing page with link to login/register."""
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "users/home.html")


def dashboard(request):
    """Dashboard: My courses and Browse all courses."""
    if not request.user.is_authenticated:
        return redirect("login")
    return render(request, "users/dashboard.html")


class RegisterView(FormView):
    form_class = UserCreationForm
    template_name = "users/register.html"
    success_url = reverse_lazy("dashboard")

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)


class CustomLoginView(LoginView):
    template_name = "users/login.html"
    redirect_authenticated_user = True


class CustomLogoutView(LogoutView):
    next_page = "home"
