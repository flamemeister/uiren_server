from django.db import models
from django.utils import timezone
from geopy.geocoders import GoogleV3
import qrcode
import io
from django.core.files.base import ContentFile
from user.models import CustomUser
from datetime import timedelta, datetime
import calendar

GOOGLE_API_KEY = 'AIzaSyBAVkETmTSFkRbC-Vix0DJ7HbjWYPQ8Xa8'

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
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)

    def __str__(self):
        return self.name

class Center(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    image = models.ImageField(upload_to='center_images/', blank=True, null=True)
    description = models.TextField(null=True, blank=True)
    about = models.TextField(null=True, blank=True)
    users = models.ManyToManyField(CustomUser, related_name='editable_centers')

    def save(self, *args, **kwargs):
        if not self.latitude or not self.longitude:
            geolocator = GoogleV3(api_key=GOOGLE_API_KEY)
            location = geolocator.geocode(self.location)
            if location:
                self.latitude = location.latitude
                self.longitude = location.longitude
            else:
                raise ValueError(f"Unable to geocode location: {self.location}")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

from datetime import timedelta, datetime
import calendar

class Section(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey('SectionCategory', related_name='sections', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='section_images/', blank=True, null=True)
    center = models.ForeignKey('Center', related_name='sections', on_delete=models.CASCADE)
    description = models.TextField(null=True, blank=True)
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, null=True)
    weekly_pattern = models.JSONField(default=list)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.qr_code:
            qr_data = {'section_id': self.id}
            qr_code_file = generate_qr_code(qr_data)
            self.qr_code.save(f'{self.name}_qr.png', qr_code_file, save=False)
            super().save(update_fields=['qr_code'])
        self.generate_static_schedule_for_next_30_days()  # Вызов правильного метода

    def generate_static_schedule_for_next_30_days(self):
        today = timezone.now().date()
        end_date = today + timedelta(days=30)  # Генерация расписания на следующие 30 дней

        # Удаление предыдущего расписания для следующих 30 дней
        Schedule.objects.filter(section=self, date__gte=today, date__lte=end_date).delete()

        # Генерация статичного расписания
        current_date = today
        while current_date <= end_date:
            day_name = current_date.strftime('%A')
            for pattern in self.weekly_pattern:
                if pattern['day'] == day_name:
                    # Проходим по всем интервалам для текущего дня
                    for interval in pattern['intervals']:
                        start_time = datetime.strptime(interval['start_time'], '%H:%M').time()
                        end_time = datetime.strptime(interval['end_time'], '%H:%M').time()

                        # Создаем запись в расписании
                        Schedule.objects.create(
                            section=self,
                            date=current_date,
                            start_time=start_time,
                            end_time=end_time,
                            capacity=20,  # Примерное значение, можно менять
                        )
            current_date += timedelta(days=1)

    def __str__(self):
        return self.name


class Subscription(models.Model):
    TYPE_CHOICES = (
        ('MONTH', 'Month'),
        ('6_MONTHS', '6 Months'),
        ('YEAR', 'Year')
    )

    name = models.CharField(max_length=255, default='Subscription')
    type = models.CharField(max_length=255, choices=TYPE_CHOICES, default='6_MONTHS')
    user = models.ForeignKey(CustomUser, related_name='subscriptions', on_delete=models.CASCADE)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_purchased = models.BooleanField(default=False)
    is_activated_by_admin = models.BooleanField(default=False)
    is_frozen = models.BooleanField(default=False)
    frozen_start_date = models.DateTimeField(null=True, blank=True)
    frozen_end_date = models.DateTimeField(null=True, blank=True)
    remaining_days = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.start_date:
            self.start_date = timezone.now()

        duration_mapping = {
            'MONTH': 30,
            '6_MONTHS': 180,
            'YEAR': 365
        }

        if not self.end_date:
            self.end_date = self.start_date + timezone.timedelta(days=duration_mapping[self.type])

        if self.is_frozen and self.frozen_end_date and self.frozen_end_date <= timezone.now():
            self.unfreeze()

        self.is_active = not self.is_frozen and self.end_date > timezone.now()
        super().save(*args, **kwargs)

    def freeze(self, freeze_days):
        """Заморозить подписку на определенное количество дней."""
        if not self.is_frozen:
            self.is_frozen = True
            self.frozen_start_date = timezone.now()
            self.frozen_end_date = timezone.now() + timedelta(days=freeze_days)
            self.remaining_days = (self.end_date - timezone.now()).days
            self.save()

    def unfreeze(self):
        """Разморозить подписку."""
        if self.is_frozen:
            self.is_frozen = False
            self.end_date = timezone.now() + timedelta(days=self.remaining_days)
            self.frozen_start_date = None
            self.frozen_end_date = None
            self.remaining_days = 0
            self.save()


        # self.is_active = self.end_date > timezone.now()
        # super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.user.email} - {self.type}"

class Schedule(models.Model):
    section = models.ForeignKey(Section, related_name='schedules', on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    capacity = models.IntegerField()
    reserved = models.IntegerField(default=0)
    status = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.reserved >= self.capacity:
            self.status = False
        else:
            self.status = True
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.section.name} on {self.date}"

class Record(models.Model):
    user = models.ForeignKey(CustomUser, related_name='records', on_delete=models.CASCADE)
    schedule = models.ForeignKey(Schedule, related_name='records', on_delete=models.CASCADE)
    attended = models.BooleanField(default=False)
    subscription = models.ForeignKey(Subscription, related_name='records', on_delete=models.CASCADE)
    is_canceled = models.BooleanField(default=False)  
    notification_sent = models.BooleanField(default=False)  

    def cancel_reservation(self):
        if not self.is_canceled:  
            if self.schedule.reserved > 0:
                self.schedule.reserved -= 1
                self.schedule.save()
            self.is_canceled = True  
            self.save()

    def __str__(self):
        return f"{self.user.email} - {self.schedule.section.name}"

class Feedback(models.Model):
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='feedbacks')
    text = models.TextField()
    stars = models.IntegerField(choices=RATING_CHOICES)
    center = models.ForeignKey('Center', on_delete=models.CASCADE, related_name='feedbacks')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback by {self.user.email} - {self.stars} Stars"