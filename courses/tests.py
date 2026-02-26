"""Tests for Course model and course list/detail views."""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .models import Course

User = get_user_model()


class CourseModelTests(TestCase):
    """Tests for the Course model."""

    def test_course_creation(self) -> None:
        """Creating a course with required fields persists correctly."""
        user = User.objects.create_user(username="teacher", password="testpass123")
        course = Course.objects.create(
            title="Introduction to Python",
            slug="intro-python",
            overview="Learn Python basics.",
            cheatsheet="print('hello')",
            created_by=user,
        )
        course.refresh_from_db()
        self.assertEqual(course.title, "Introduction to Python")
        self.assertEqual(course.slug, "intro-python")
        self.assertEqual(course.overview, "Learn Python basics.")
        self.assertEqual(course.cheatsheet, "print('hello')")
        self.assertEqual(course.created_by, user)
        self.assertTrue(course.has_questions)
        self.assertFalse(course.has_flashcards)


class CourseListViewTests(TestCase):
    """Tests for the course list view."""

    def test_course_list_returns_200(self) -> None:
        """Anonymous user can view course list."""
        client = Client()
        response = client.get(reverse("courses:list"))
        self.assertEqual(response.status_code, 200)

    def test_course_list_uses_template(self) -> None:
        """Course list renders the correct template."""
        client = Client()
        response = client.get(reverse("courses:list"))
        self.assertTemplateUsed(response, "courses/course_list.html")

    def test_course_list_shows_courses_in_context(self) -> None:
        """Course list context contains courses ordered by created_at."""
        user = User.objects.create_user(username="teacher", password="testpass123")
        Course.objects.create(
            title="Course A",
            slug="course-a",
            overview="A",
            cheatsheet="a",
            created_by=user,
        )
        Course.objects.create(
            title="Course B",
            slug="course-b",
            overview="B",
            cheatsheet="b",
            created_by=user,
        )
        client = Client()
        response = client.get(reverse("courses:list"))
        self.assertEqual(response.status_code, 200)
        courses = list(response.context["courses"])
        self.assertEqual(len(courses), 2)
        # Newest first
        self.assertEqual(courses[0].slug, "course-b")
        self.assertEqual(courses[1].slug, "course-a")


class CourseDetailViewTests(TestCase):
    """Tests for the course detail view."""

    def test_course_detail_returns_200_for_valid_slug(self) -> None:
        """Course detail returns 200 when slug exists."""
        user = User.objects.create_user(username="teacher", password="testpass123")
        Course.objects.create(
            title="My Course",
            slug="my-course",
            overview="Overview.",
            cheatsheet="Cheatsheet.",
            created_by=user,
        )
        client = Client()
        response = client.get(reverse("courses:detail", kwargs={"slug": "my-course"}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["course"].slug, "my-course")

    def test_course_detail_returns_404_for_invalid_slug(self) -> None:
        """Course detail returns 404 when slug does not exist."""
        client = Client()
        response = client.get(reverse("courses:detail", kwargs={"slug": "nonexistent-slug"}))
        self.assertEqual(response.status_code, 404)

    def test_course_detail_uses_template(self) -> None:
        """Course detail renders the correct template."""
        user = User.objects.create_user(username="teacher", password="testpass123")
        Course.objects.create(
            title="My Course",
            slug="my-course",
            overview="Overview.",
            cheatsheet="Cheatsheet.",
            created_by=user,
        )
        client = Client()
        response = client.get(reverse("courses:detail", kwargs={"slug": "my-course"}))
        self.assertTemplateUsed(response, "courses/course_detail.html")
