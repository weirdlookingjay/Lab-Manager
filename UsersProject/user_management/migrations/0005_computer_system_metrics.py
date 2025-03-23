from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('user_management', '0004_alter_computer_options_and_more'),
    ]

    operations = [
        # Remove old fields
        migrations.RemoveField(
            model_name='computer',
            name='cpu_percent',
        ),
        migrations.RemoveField(
            model_name='computer',
            name='memory_percent',
        ),
        migrations.RemoveField(
            model_name='computer',
            name='network_info',
        ),
        migrations.RemoveField(
            model_name='computer',
            name='cpu_frequency_current',
        ),
        migrations.RemoveField(
            model_name='computer',
            name='cpu_frequency_min',
        ),
        migrations.RemoveField(
            model_name='computer',
            name='cpu_frequency_max',
        ),
        migrations.RemoveField(
            model_name='computer',
            name='is_online',
        ),
        
        # Add new fields
        migrations.AddField(
            model_name='computer',
            name='cpu_model',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='computer',
            name='cpu_speed',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='computer',
            name='cpu_architecture',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='computer',
            name='device_class',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='computer',
            name='system_uptime',
            field=models.DurationField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='computer',
            name='disk_total',
            field=models.BigIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='computer',
            name='disk_free',
            field=models.BigIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='computer',
            name='disk_used',
            field=models.BigIntegerField(blank=True, null=True),
        ),
        
        # Rename fields
        migrations.RenameField(
            model_name='computer',
            old_name='cpu_count',
            new_name='cpu_threads',
        ),
        migrations.RenameField(
            model_name='computer',
            old_name='cpu_physical_count',
            new_name='cpu_cores',
        ),
    ]
