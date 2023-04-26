# Generated by Django 3.2.18 on 2023-04-05 20:38

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("tools", "0031_merge_20230301_2012"),
    ]

    operations = [
        migrations.AlterField(
            model_name="organizationmember",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, related_name="members", to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
