# Generated by Django 5.0.5 on 2024-08-07 08:27

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0008_alter_subscription_expiration_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscription',
            name='expiration_date',
            field=models.DateTimeField(default=datetime.datetime(2024, 9, 6, 8, 27, 21, 127362, tzinfo=datetime.timezone.utc)),
        ),
    ]
