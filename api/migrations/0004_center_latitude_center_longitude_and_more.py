# Generated by Django 5.0.5 on 2024-08-13 11:45

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_alter_subscription_expiration_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='center',
            name='latitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='center',
            name='longitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='expiration_date',
            field=models.DateTimeField(default=datetime.datetime(2024, 9, 12, 11, 45, 21, 740239, tzinfo=datetime.timezone.utc)),
        ),
    ]
