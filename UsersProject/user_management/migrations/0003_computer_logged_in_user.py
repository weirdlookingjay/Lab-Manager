# Generated by Django 4.2.18 on 2025-03-11 16:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user_management", "0002_auto_20250307_1408"),
    ]

    operations = [
        migrations.AddField(
            model_name="computer",
            name="logged_in_user",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
