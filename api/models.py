from django.db import models
from django.conf import settings
from django.utils import timezone

class Center(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)

    def __str__(self):
        return self.name

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
        # Check for more than 3 enrollments per subscription per day
        enrollments_on_same_day = Enrollment.objects.filter(
            subscription=self.subscription,
            time__date=self.time.date()
        ).count()
        if enrollments_on_same_day >= 3:
            raise ValidationError('You cannot have more than 3 enrollments per subscription per day.')

        # Check for overlapping times
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
