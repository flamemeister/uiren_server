from django.db import models
from django.conf import settings
from django.utils import timezone
import qrcode
import io
from django.core.files.base import ContentFile

def generate_qr_code(data):
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
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

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.qr_code:
            qr_code_file = generate_qr_code(f'{self.id}')
            self.qr_code.save(f'{self.name}_qr.png', qr_code_file, save=False)
        super().save(*args, **kwargs)


class SectionCategory(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Section(models.Model):
    center = models.ForeignKey(Center, related_name='sections', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    category = models.ForeignKey(SectionCategory, related_name='sections', on_delete=models.CASCADE, null=True, blank=True)
    schedule = models.JSONField(default=dict, null=True, blank=True)
    available_times = models.JSONField(default=list, null=True, blank=True)

    def __str__(self):
        return self.name

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
