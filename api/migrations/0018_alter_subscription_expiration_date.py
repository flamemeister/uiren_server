# Generated by Django 5.0.5 on 2024-08-12 10:21

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0017_remove_section_schedule_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscription',
            name='expiration_date',
            field=models.DateTimeField(default=datetime.datetime(2024, 9, 11, 10, 21, 58, 669346, tzinfo=datetime.timezone.utc)),
        ),
    ]
