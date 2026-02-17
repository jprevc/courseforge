from django.urls import path

from . import views

app_name = "courses"

urlpatterns = [
    path("", views.course_list, name="list"),
    path("create/", views.course_create, name="create"),
    path("<slug:slug>/", views.course_detail, name="detail"),
    path("<slug:slug>/start/", views.course_start, name="start"),
    path("<slug:slug>/exercise/<int:index>/", views.exercise_view, name="exercise"),
]
