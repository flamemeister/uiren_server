from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

class CustomUserManager(BaseUserManager):
    def create_user(self, email=None, phone_number=None, first_name=None, last_name=None, password=None, **extra_fields):
        if not email and not phone_number:
            raise ValueError('Either email or phone number must be provided')

        if email:
            email = self.normalize_email(email)

        user = self.model(
            email=email,
            phone_number=phone_number,
            first_name=first_name,
            last_name=last_name,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, first_name, last_name, phone_number, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('USER', 'User'),
        ('ADMIN', 'Admin'),
        ('CHILD', 'Child'),
        ('PARENT', 'Parent')
    )

    email = models.EmailField(unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)  # Allow phone_number as a unique field
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    iin = models.CharField(max_length=12, unique=True, null=True, blank=True)
    role = models.CharField(max_length=6, choices=ROLE_CHOICES, default='USER')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)  # Add is_staff for admin purposes
    is_superuser = models.BooleanField(default=False)  # Add is_superuser for permissions
    is_verified = models.BooleanField(default=False)  # This indicates if the account is verified via email or SMS
    date_joined = models.DateTimeField(default=timezone.now)
    sms_code = models.CharField(max_length=6, null=True, blank=True)  # Add this to store the SMS code

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'  # Email by default; we will override this in views for phone number
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email or self.phone_number
