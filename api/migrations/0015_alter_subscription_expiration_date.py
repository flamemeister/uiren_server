# Generated by Django 5.0.5 on 2024-08-07 12:22

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0014_alter_subscription_expiration_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscription',
            name='expiration_date',
            field=models.DateTimeField(default=datetime.datetime(2024, 9, 6, 12, 22, 7, 523093, tzinfo=datetime.timezone.utc)),
        ),
    ]
