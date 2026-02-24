import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0003_add_course_generation_model"),
    ]

    operations = [
        migrations.AddField(
            model_name="course",
            name="has_questions",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="course",
            name="has_flashcards",
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name="Flashcard",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("order_index", models.PositiveIntegerField(default=0)),
                ("front", models.TextField()),
                ("back", models.TextField()),
                (
                    "course",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="flashcards",
                        to="courses.course",
                    ),
                ),
            ],
            options={
                "ordering": ["course", "order_index"],
                "unique_together": {("course", "order_index")},
            },
        ),
    ]
