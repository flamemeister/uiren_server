from rest_framework import serializers
from .models import CustomUser
from .utils import generate_random_password 
from .utils import send_verification_email
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils.http import urlsafe_base64_decode


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'phone_number', 'iin', 'date_joined', 'is_active', 'is_staff', 'role']

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        instance.iin = validated_data.get('iin', instance.iin)  
        instance.role = validated_data.get('role', instance.role)

        instance.save()
        return instance


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, default=generate_random_password, required=False)

    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'phone_number', 'iin', 'password', 'role')

    def create(self, validated_data):
        password = validated_data.get('password') or generate_random_password()
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone_number=validated_data['phone_number'],
            iin=validated_data['iin'],
            password=password,
            role=validated_data['role'],
            is_active=False,  # Учетная запись неактивна до подтверждения
        )
        
        request = self.context.get('request')
        send_verification_email(user, request)  # Отправка письма с подтверждением
        return user

class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'first_name', 'last_name', 'phone_number', 'iin', 'role')  

User = get_user_model()

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Пользователь с таким email не найден.")
        return value

    def save(self):
        request = self.context.get('request')
        email = self.validated_data['email']
        user = User.objects.get(email=email)

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        reset_link = f"{request.build_absolute_uri('/password-reset-confirm/')}?uid={uid}&token={token}"
        
        send_mail(
            subject="Сброс пароля",
            message=f"Для сброса пароля перейдите по следующей ссылке: {reset_link}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )

class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)
    uid = serializers.CharField()
    token = serializers.CharField()

    def validate(self, attrs):
        try:
            uid = attrs.get('uid')
            token = attrs.get('token')
            user_id = urlsafe_base64_decode(uid).decode()
            user = User.objects.get(pk=user_id)

            if not default_token_generator.check_token(user, token):
                raise serializers.ValidationError('Неверный токен или UID.')
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError('Неверный токен или UID.')
        return attrs

    def save(self):
        uid = self.validated_data.get('uid')
        user_id = urlsafe_base64_decode(uid).decode()
        user = User.objects.get(pk=user_id)
        user.set_password(self.validated_data.get('new_password'))
        user.save()
        return user



