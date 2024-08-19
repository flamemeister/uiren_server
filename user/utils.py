import random
import string
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings

def generate_random_password(length=8):
    return ''.join(random.choices(string.digits, k=length))

def send_verification_email(user, request):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    verification_link = f"{request.build_absolute_uri('/user/verify-email/')}?uid={uid}&token={token}"
    
    send_mail(
        subject="Подтверждение регистрации",
        message=f"Для подтверждения учетной записи перейдите по ссылке: {verification_link}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )

