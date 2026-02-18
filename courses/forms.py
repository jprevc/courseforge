"""Forms for course creation and other course-related input."""

from django import forms


class CreateCourseForm(forms.Form):
    """Form to submit a topic string for AI-generated course creation."""

    topic = forms.CharField(
        max_length=255,
        label="Topic",
        widget=forms.TextInput(
            attrs={
                "placeholder": "e.g. Python list comprehensions",
                "size": 50,
            }
        ),
    )
