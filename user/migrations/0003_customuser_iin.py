# Generated by Django 5.0.5 on 2024-08-13 06:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0002_remove_customuser_iin_remove_customuser_birthdate'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='iin',
            field=models.CharField(blank=True, max_length=12, null=True, unique=True),
        ),
    ]
