# Generated by Django 5.0.5 on 2024-08-12 10:27

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0018_alter_subscription_expiration_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscription',
            name='expiration_date',
            field=models.DateTimeField(default=datetime.datetime(2024, 9, 11, 10, 27, 23, 534224, tzinfo=datetime.timezone.utc)),
        ),
    ]
