# Generated by Django 3.2.5 on 2021-12-23 10:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="FailureMode",
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
                ("failure_mode", models.CharField(max_length=256)),
                (
                    "severity_level",
                    models.PositiveSmallIntegerField(
                        choices=[
                            ("", "--- Select an option ----"),
                            (1, "1. Not Severe"),
                            (2, "2. Harmful"),
                            (3, "3. Severe"),
                            (4, "4. Very Harmful"),
                            (5, "5. Catastrophic"),
                        ]
                    ),
                ),
                (
                    "frequency_level",
                    models.PositiveSmallIntegerField(
                        choices=[
                            ("", "--- Select an option ----"),
                            (
                                1,
                                "1. Very Rare. Incident (almost) never occurs, almost unthinkable.",
                            ),
                            (
                                2,
                                "2. Rare. Incidents occur less than once a year (3-5).",
                            ),
                            (3, "3. Occurs. Incidents occur several times a year."),
                            (4, "4. Regularly. Incidents occur weekly."),
                            (5, "5. Frequent. Incidents occur daily."),
                        ]
                    ),
                ),
                (
                    "detectability_level",
                    models.PositiveSmallIntegerField(
                        choices=[
                            ("", "--- Select an option ----"),
                            (
                                1,
                                "1. Always Detectable. Incident (almost) never occurs, almost unthinkable.",
                            ),
                            (
                                2,
                                "2. Usually Detectable. Incidents occur less than once a year (3-5).",
                            ),
                            (
                                3,
                                "3. Detectable. Faillure mode is detectable with effort.",
                            ),
                            (
                                4,
                                "4. Poorly Detectable. Detecting the faillure mode is difficult.",
                            ),
                            (
                                5,
                                "5. Almost Undetectable. "
                                "Failure mode detection is very difficult or nearly impossible.",
                            ),
                        ]
                    ),
                ),
                ("risk_class", models.CharField(blank=True, max_length=50, null=True)),
                ("effect", models.CharField(blank=True, max_length=256)),
                ("description", models.CharField(blank=True, max_length=256)),
            ],
            options={
                "verbose_name_plural": "Failure modes",
            },
        ),
        migrations.CreateModel(
            name="FailureModeDepartment",
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
                (
                    "affected_department",
                    models.PositiveSmallIntegerField(
                        choices=[
                            ("", "--- Select an option ----"),
                            (1, "Finances"),
                            (2, "Marketing"),
                            (3, "Human Resources"),
                            (4, "Research & Development"),
                            (5, "Administration"),
                            (6, "Service"),
                        ]
                    ),
                ),
                (
                    "failure_mode",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="fmea.failuremode",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Failure Mode Departments",
            },
        ),
    ]