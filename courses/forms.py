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
        ("", "Agent decides"),
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
    include_questions = forms.BooleanField(
        required=False,
        initial=True,
        label="Generate questions",
    )
    include_flashcards = forms.BooleanField(
        required=False,
        label="Generate flashcards",
    )
    num_exercises = forms.TypedChoiceField(
        choices=NUM_EXERCISES_CHOICES,
        coerce=lambda v: int(v) if v != "" else None,
        required=False,
        label="Number of exercises",
        help_text="Short quiz (3) to longer course (10). Leave blank to let the agent decide.",
    )
    num_flashcards = forms.TypedChoiceField(
        choices=[("", "Agent decides"), (5, "5"), (10, "10"), (15, "15"), (20, "20")],
        coerce=lambda v: int(v) if v != "" else None,
        required=False,
        label="Number of flashcards",
        help_text="Leave blank to let the agent decide.",
    )

    def clean(self):
        cleaned_data = super().clean()
        include_questions = cleaned_data.get("include_questions")
        include_flashcards = cleaned_data.get("include_flashcards")

        if not include_questions and not include_flashcards:
            raise forms.ValidationError("Select at least one of Questions or Flashcards.")

        return cleaned_data
