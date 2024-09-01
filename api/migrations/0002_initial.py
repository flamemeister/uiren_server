# Generated by Django 4.2.6 on 2024-09-01 18:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='purchased_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='purchased_subscriptions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='subscription',
            name='section',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='subscriptions', to='api.section'),
        ),
        migrations.AddField(
            model_name='subscription',
            name='user',
            field=models.ForeignKey(db_column='iin', on_delete=django.db.models.deletion.CASCADE, related_name='subscriptions', to=settings.AUTH_USER_MODEL, to_field='iin'),
        ),
        migrations.AddField(
            model_name='section',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sections', to='api.sectioncategory'),
        ),
        migrations.AddField(
            model_name='schedule',
            name='center',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='schedules', to='api.center'),
        ),
        migrations.AddField(
            model_name='schedule',
            name='section',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='schedules', to='api.section'),
        ),
        migrations.AddField(
            model_name='payment',
            name='center',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='api.center'),
        ),
        migrations.AddField(
            model_name='payment',
            name='section',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='api.section'),
        ),
        migrations.AddField(
            model_name='payment',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='feedback',
            name='center',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feedbacks', to='api.center'),
        ),
        migrations.AddField(
            model_name='feedback',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feedbacks', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='enrollment',
            name='section',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrollments', to='api.section'),
        ),
        migrations.AddField(
            model_name='enrollment',
            name='subscription',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrollments', to='api.subscription'),
        ),
        migrations.AddField(
            model_name='enrollment',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrollments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='center',
            name='sections',
            field=models.ManyToManyField(related_name='centers', to='api.section'),
        ),
    ]
