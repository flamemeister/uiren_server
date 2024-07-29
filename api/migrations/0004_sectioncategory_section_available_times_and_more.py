# Generated by Django 5.0.5 on 2024-07-29 11:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_enrollment_confirmation_time_enrollment_confirmed'),
    ]

    operations = [
        migrations.CreateModel(
            name='SectionCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
            ],
        ),
        migrations.AddField(
            model_name='section',
            name='available_times',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='section',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sections', to='api.sectioncategory'),
        ),
    ]
