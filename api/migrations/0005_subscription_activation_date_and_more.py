# Generated by Django 4.2.6 on 2024-08-04 18:29

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_center_qr_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='activation_date',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2024, 8, 4, 18, 29, 47, 860622, tzinfo=datetime.timezone.utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='subscription',
            name='expiration_date',
            field=models.DateTimeField(default=datetime.datetime(2024, 9, 3, 18, 29, 9, 501897, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AddField(
            model_name='subscription',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
