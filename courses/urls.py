from django.urls import path, register_converter

from . import views


class UnicodeSlugConverter:
    """Path converter that accepts Unicode slug characters (e.g. ž, č, š).

    Django's built-in slug converter only matches ASCII; our Course slug uses
    allow_unicode=True, so we need this for URLs like /courses/kužne-bolezni-v-tropskih-krajih/
    """

    regex = r"[-\w]+"

    def to_python(self, value: str) -> str:
        return value

    def to_url(self, value: str) -> str:
        return value


register_converter(UnicodeSlugConverter, "uslug")

app_name = "courses"

urlpatterns = [
    path("", views.course_list, name="list"),
    path("create/", views.course_create, name="create"),
    path("generating/<uuid:job_id>/", views.generating_view, name="generating"),
    path("api/job-status/<uuid:job_id>/", views.job_status_api, name="job_status"),
    path("api/notifications/", views.api_notifications, name="notifications"),
    path("api/notifications/mark-all-read/", views.api_mark_all_notifications_read, name="notifications_mark_read"),
    path("<uslug:slug>/", views.course_detail, name="detail"),
    path("<uslug:slug>/start/", views.course_start, name="start"),
    path("<uslug:slug>/flashcards/", views.flashcards_view, name="flashcards"),
    path("<uslug:slug>/exercise/<int:index>/", views.exercise_view, name="exercise"),
]
