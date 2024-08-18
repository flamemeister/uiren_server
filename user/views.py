from rest_framework import generics, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from .models import CustomUser
from .serializers import CustomUserSerializer, RegisterSerializer, UserDetailSerializer

class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    # permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return UserDetailSerializer
        elif self.action == 'create':
            return RegisterSerializer
        else:
            return CustomUserSerializer

    # def get_permissions(self):
    #     if self.action in ['list', 'retrieve']:
    #         return [IsAuthenticated()]
    #     elif self.action == 'create':
    #         return [IsAuthenticated()]
    #     else:
    #         return [IsAdminUser()]

class UserByTokenView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserDetailSerializer

    def get_object(self):
        return self.request.user

from rest_framework import generics, permissions
from .models import CustomUser
from .serializers import CustomUserSerializer

class UserProfileView(generics.RetrieveUpdateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
    
from django.utils.http import urlsafe_base64_decode
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.contrib.auth.tokens import default_token_generator

User = get_user_model()

class VerifyEmailView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        uid = request.query_params.get('uid')
        token = request.query_params.get('token')

        try:
            user_id = urlsafe_base64_decode(uid).decode()
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({'error': 'Неверный идентификатор пользователя'}, status=400)

        if default_token_generator.check_token(user, token):
            user.is_verified = True
            user.is_active = True
            user.save()
            return Response({'detail': 'Аккаунт успешно подтвержден.'})
        else:
            return Response({'error': 'Неверный токен'}, status=400)

