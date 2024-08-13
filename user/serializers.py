from rest_framework import serializers
from .models import CustomUser
from rest_framework import serializers
from .models import CustomUser
from .utils import generate_random_password  

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
        )
        return user


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'first_name', 'last_name', 'phone_number', 'iin', 'role')  

