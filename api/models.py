from django.db import models
from django.conf import settings
from django.utils import timezone
import qrcode
import io
from django.core.files.base import ContentFile
import json
from user.models import CustomUser
from geopy.geocoders import GoogleV3
from django.core.exceptions import ValidationError

def generate_qr_code(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buf = io.BytesIO()
    img.save(buf)
    image_stream = buf.getvalue()
    return ContentFile(image_stream)

class SectionCategory(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Section(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(SectionCategory, related_name='sections', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        for center in self.centers.all():
            center.save()

class Center(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    sections = models.ManyToManyField(Section, related_name='centers')  # Множество секций, связанных с центром
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, null=True)
    link = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.latitude or not self.longitude:
            geolocator = GoogleV3(api_key='AIzaSyCN-x4jF1BZ9UoWD144d4vH4ocal-EDz5k')
            location = geolocator.geocode(self.location)
            if location:
                self.latitude = location.latitude
                self.longitude = location.longitude
            else:
                raise ValidationError('Не удалось преобразовать адрес в координаты.')

        super(Center, self).save(*args, **kwargs)

        if not self.qr_code:
            subscriptions = Subscription.objects.filter(center=self)

            data = {
                'center_id': self.id,
                'center_name': self.name,
                'subscriptions': [
                    {
                        'subscription_id': subscription.id,
                        'user_id': subscription.user.id,
                    }
                    for subscription in subscriptions
                ],
                'sections': list(self.sections.values('id', 'name'))
            }

            if subscriptions.exists():
                data['subscription_id'] = subscriptions.first().id

            qr_code_file = generate_qr_code(json.dumps(data))
            self.qr_code.save(f'{self.name}_qr.png', qr_code_file, save=False)
            self.save(update_fields=['qr_code'])

class Schedule(models.Model):
    center = models.ForeignKey(Center, related_name='schedules', on_delete=models.CASCADE)
    section = models.ForeignKey(Section, related_name='schedules', on_delete=models.CASCADE)
    day_of_week = models.CharField(max_length=9, choices=[
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday')
    ])
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.center.name} - {self.section.name} on {self.day_of_week} from {self.start_time} to {self.end_time}"

class Subscription(models.Model):
    TYPE_CHOICES = (
        ('8 уроков', '8 уроков'),
        ('10 уроков', '10 уроков'),
        ('12 уроков', '12 уроков')
    )
    purchased_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='purchased_subscriptions', null=True, blank=True)
    user = models.ForeignKey(CustomUser, related_name='subscriptions', on_delete=models.CASCADE)  # Связь по ID пользователя
    center = models.ForeignKey(Center, related_name='subscriptions', on_delete=models.CASCADE)
    section = models.ForeignKey(Section, related_name='subscriptions', on_delete=models.CASCADE, null=True, blank=True)
    type = models.CharField(max_length=255, choices=TYPE_CHOICES)
    name = models.CharField(max_length=255)
    activation_date = models.DateTimeField(auto_now_add=True)
    expiration_date = models.DateTimeField(default=timezone.now() + timezone.timedelta(days=30))
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.type} ({self.user.email})"

class Enrollment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='enrollments', on_delete=models.CASCADE)
    section = models.ForeignKey(Section, related_name='enrollments', on_delete=models.CASCADE)
    subscription = models.ForeignKey(Subscription, related_name='enrollments', on_delete=models.CASCADE)
    time = models.DateTimeField()
    confirmed = models.BooleanField(default=False)
    confirmation_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} - {self.section.name}"

    def clean(self):
        from django.core.exceptions import ValidationError
        enrollments_on_same_day = Enrollment.objects.filter(
            subscription=self.subscription,
            time__date=self.time.date()
        ).count()
        if enrollments_on_same_day >= 5:
            raise ValidationError('You cannot have more than 5 enrollments per subscription per day.')

        overlapping_enrollments = Enrollment.objects.filter(
            subscription=self.subscription,
            time__gte=self.time - timezone.timedelta(hours=1),
            time__lte=self.time + timezone.timedelta(hours=1)
        ).exists()
        if overlapping_enrollments:
            raise ValidationError('There must be at least 1 hour between enrollments.')

class Feedback(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='feedbacks', on_delete=models.CASCADE)
    center = models.ForeignKey(Center, related_name='feedbacks', on_delete=models.CASCADE)
    feedback = models.TextField()

    def __str__(self):
        return f"Feedback by {self.user.email} for {self.center.name}"

class Payment(models.Model):
    txn_id = models.CharField(max_length=100, unique=True)
    student = models.ForeignKey(CustomUser, related_name='payments', on_delete=models.CASCADE)  # Внешний ключ на CustomUser
    center = models.ForeignKey(Center, related_name='payments', on_delete=models.CASCADE)  # Внешний ключ на Center
    section = models.ForeignKey(Section, related_name='payments', on_delete=models.CASCADE)  # Внешний ключ на Section
    payment_period = models.CharField(max_length=50, blank=True, null=True)  # Обновление поля
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.email} - {self.center.name} - {self.amount}"

