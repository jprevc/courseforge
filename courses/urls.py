from django.urls import path

from . import views

app_name = "courses"

urlpatterns = [
    path("", views.course_list, name="list"),
    path("create/", views.course_create, name="create"),
    path("generating/<uuid:job_id>/", views.generating_view, name="generating"),
    path("api/job-status/<uuid:job_id>/", views.job_status_api, name="job_status"),
    path("<slug:slug>/", views.course_detail, name="detail"),
    path("<slug:slug>/start/", views.course_start, name="start"),
    path("<slug:slug>/exercise/<int:index>/", views.exercise_view, name="exercise"),
]
