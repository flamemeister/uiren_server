from django.db import models
from django.conf import settings
from django.utils import timezone
import qrcode
import io
from django.core.files.base import ContentFile
import json

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

class Center(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, null=True)
    link = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        creating = self.pk is None
        super(Center, self).save(*args, **kwargs)

        if creating and not self.qr_code:
            data = {
                'center_id': self.id,
                'center_name': self.name,
                'sections': list(self.sections.values('id', 'name'))
            }
            qr_code_file = generate_qr_code(json.dumps(data))
            self.qr_code.save(f'{self.name}_qr.png', qr_code_file, save=False)
            self.save(update_fields=['qr_code'])

class SectionCategory(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Section(models.Model):
    center = models.ForeignKey(Center, related_name='sections', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    category = models.ForeignKey(SectionCategory, related_name='sections', on_delete=models.CASCADE, null=True, blank=True)
    available_times = models.JSONField(default=list, null=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.center.save()  

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

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='subscriptions', on_delete=models.CASCADE)
    center = models.ForeignKey(Center, related_name='subscriptions', on_delete=models.CASCADE)
    section = models.ForeignKey(Section, related_name='subscriptions', on_delete=models.CASCADE, null=True, blank=True)
    type = models.CharField(max_length=255, choices=TYPE_CHOICES)
    name = models.CharField(max_length=255)
    activation_date = models.DateTimeField(auto_now_add=True)
    expiration_date = models.DateTimeField(default=timezone.now() + timezone.timedelta(days=30))
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.type}"

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
        if enrollments_on_same_day >= 3:
            raise ValidationError('You cannot have more than 3 enrollments per subscription per day.')

        overlapping_enrollments = Enrollment.objects.filter(
            subscription=self.subscription,
            time=self.time
        ).exists()
        if overlapping_enrollments:
            raise ValidationError('Enrollment times cannot overlap.')

class Feedback(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='feedbacks', on_delete=models.CASCADE)
    center = models.ForeignKey(Center, related_name='feedbacks', on_delete=models.CASCADE)
    feedback = models.TextField()

    def __str__(self):
        return f"Feedback by {self.user.email} for {self.center.name}"
