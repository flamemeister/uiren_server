from django.db import models
from django.utils import timezone
from geopy.geocoders import GoogleV3
import qrcode
import io
from django.core.files.base import ContentFile
from user.models import CustomUser  # Assume this exists

# QR Code Generation Utility
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

# Section Category Model
class SectionCategory(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)

    def __str__(self):
        return self.name

# Section Model
class Section(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(SectionCategory, related_name='sections', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='section_images/', blank=True, null=True)
    centers = models.ManyToManyField('Center', related_name='sections')
    description = models.TextField(null=True, blank=True)  # New description field

    def __str__(self):
        return self.name

# Center Model
# Center Model
class Center(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)  # Address or location that will be geocoded
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, null=True)
    image = models.ImageField(upload_to='center_images/', blank=True, null=True)
    description = models.TextField(null=True, blank=True)  # New description field

    def save(self, *args, **kwargs):
        # Geocode the location if latitude or longitude is missing
        if not self.latitude or not self.longitude:
            geolocator = GoogleV3(api_key='AIzaSyCN-x4jF1BZ9UoWD144d4vH4ocal-EDz5k')  # Replace with your Google API key
            location = geolocator.geocode(self.location)
            if location:
                self.latitude = location.latitude
                self.longitude = location.longitude
            else:
                raise ValueError(f"Unable to geocode location: {self.location}")

        # Save the object first to ensure it has an ID
        super().save(*args, **kwargs)
        
        # Generate QR Code if it doesn't exist
        if not self.qr_code:
            qr_data = {'center_id': self.id}
            qr_code_file = generate_qr_code(qr_data)
            self.qr_code.save(f'{self.name}_qr.png', qr_code_file, save=False)
            
            # Save the updated qr_code field
            super().save(update_fields=['qr_code'])

    def __str__(self):
        return self.name



# Subscription Model
class Subscription(models.Model):
    TYPE_CHOICES = (
        ('MONTH', 'Month'),
        ('6_MONTHS', '6 Months'),
        ('YEAR', 'Year')
    )
    user = models.ForeignKey(CustomUser, related_name='subscriptions', on_delete=models.CASCADE)
    section = models.ForeignKey(Section, related_name='subscriptions', on_delete=models.CASCADE)
    type = models.CharField(max_length=255, choices=TYPE_CHOICES)
    start_date = models.DateTimeField(default=timezone.now)  # Set start_date automatically
    end_date = models.DateTimeField(null=True, blank=True)  # Will be calculated based on type
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        # Ensure start_date is set properly
        if not self.start_date:
            self.start_date = timezone.now()
        
        # Define the end date based on subscription type
        duration_mapping = {
            'MONTH': 30,
            '6_MONTHS': 180,
            'YEAR': 365
        }
        # If no end_date is provided, calculate it based on the subscription type
        if not self.end_date:
            self.end_date = self.start_date + timezone.timedelta(days=duration_mapping[self.type])

        # Call the parent class's save method to save the object
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} - {self.section.name}"

# Schedule Model
class Schedule(models.Model):
    section = models.ForeignKey(Section, related_name='schedules', on_delete=models.CASCADE)
    center = models.ForeignKey(Center, related_name='schedules', on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    capacity = models.IntegerField()
    reserved = models.IntegerField(default=0)
    status = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.reserved >= self.capacity:
            self.status = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.center.name} - {self.section.name} on {self.date}"

# Record Model
class Record(models.Model):
    user = models.ForeignKey(CustomUser, related_name='records', on_delete=models.CASCADE)
    schedule = models.ForeignKey(Schedule, related_name='records', on_delete=models.CASCADE)
    attended = models.BooleanField(default=False)
    section = models.ForeignKey(Section, related_name='records', on_delete=models.CASCADE)  # Track section directly

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
    center = models.ForeignKey('Center', on_delete=models.CASCADE, related_name='feedbacks')  # Assuming feedback is for a Center

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback by {self.user.email} - {self.stars} Stars"
