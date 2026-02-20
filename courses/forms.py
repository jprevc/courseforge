"""Forms for course creation and other course-related input."""

from django import forms


class CreateCourseForm(forms.Form):
    """Form to submit a topic and options for AI-generated course creation."""

    DIFFICULTY_CHOICES = [
        ("beginner", "Beginner"),
        ("intermediate", "Intermediate"),
        ("advanced", "Advanced"),
    ]

    NUM_EXERCISES_CHOICES = [
        (3, "3"),
        (5, "5"),
        (8, "8"),
        (10, "10"),
    ]

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
    difficulty = forms.ChoiceField(
        choices=DIFFICULTY_CHOICES,
        label="Difficulty",
        initial="beginner",
        help_text="Shapes vocabulary, depth, and exercise difficulty.",
    )
    additional_instructions = forms.CharField(
        required=False,
        max_length=500,
        label="Additional instructions",
        widget=forms.Textarea(
            attrs={
                "placeholder": "e.g. focus on async/await, use real-world examples",
                "rows": 3,
            }
        ),
        help_text="Optional. Free-form guidance for the course (max 500 characters).",
    )
    num_exercises = forms.TypedChoiceField(
        choices=NUM_EXERCISES_CHOICES,
        coerce=int,
        label="Number of exercises",
        initial=5,
        help_text="Short quiz (3) to longer course (10).",
    )
