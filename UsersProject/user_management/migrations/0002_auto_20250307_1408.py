# Generated by Django 4.2.18 on 2025-03-07 19:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user_management", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name='computer',
            name='hostname',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
