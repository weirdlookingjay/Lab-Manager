# Generated by Django 4.2.18 on 2025-02-14 20:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tickets", "0002_routingrule"),
    ]

    operations = [
        migrations.AddField(
            model_name="routingrule",
            name="actions",
            field=models.JSONField(default=dict),
        ),
    ]
