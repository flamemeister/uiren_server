from django.db import models
from django.conf import settings

class Center(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Section(models.Model):
    center = models.ForeignKey(Center, related_name='sections', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    schedule = models.TextField()

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
    type = models.CharField(max_length=255, choices=TYPE_CHOICES)
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name} - {self.type}"

class Enrollment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='enrollments', on_delete=models.CASCADE)
    section = models.ForeignKey(Section, related_name='enrollments', on_delete=models.CASCADE)
    time = models.DateTimeField()
    confirmed = models.BooleanField(default=False)
    confirmation_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} - {self.section.name}"

class Feedback(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='feedbacks', on_delete=models.CASCADE)
    center = models.ForeignKey(Center, related_name='feedbacks', on_delete=models.CASCADE)
    feedback = models.TextField()

    def __str__(self):
        return f"Feedback by {self.user.email} for {self.center.name}"
