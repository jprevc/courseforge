from django import forms


class CreateCourseForm(forms.Form):
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
