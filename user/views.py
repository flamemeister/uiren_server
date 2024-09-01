from rest_framework import generics, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from .models import CustomUser
from .serializers import CustomUserSerializer, RegisterSerializer, UserDetailSerializer
from .serializers import PasswordResetConfirmSerializer

class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer
    
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import CustomUser
from .serializers import CustomUserSerializer, RegisterSerializer, UserDetailSerializer
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import permissions

class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return UserDetailSerializer
        elif self.action == 'create':
            return RegisterSerializer
        else:
            return CustomUserSerializer

    def get_permissions(self):
        if self.action in ['create', 'password_reset', 'register']:
            return [permissions.AllowAny()]
        elif self.action in ['add_child']:
            return [IsAuthenticated()]
        else:
            return [IsAdminUser()]

    @action(detail=True, methods=['post'], url_path='add-child', permission_classes=[IsAuthenticated])
    def add_child(self, request, pk=None):
        parent = self.get_object()
        if parent.role != 'ADMIN':
            return Response({'error': 'Only parents can add children.'}, status=status.HTTP_403_FORBIDDEN)
        
        child_id = request.data.get('child_id')
        if not child_id:
            return Response({'error': 'child_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            child = CustomUser.objects.get(id=child_id)
            if child.parent is not None:
                return Response({'error': 'This child is already linked to a parent.'}, status=status.HTTP_400_BAD_REQUEST)
            child.parent = parent
            child.save()
            return Response({'status': 'Child added successfully'}, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({'error': 'Child not found.'}, status=status.HTTP_404_NOT_FOUND)

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

from rest_framework import generics
from rest_framework.permissions import AllowAny
from .serializers import PasswordResetRequestSerializer

class PasswordResetRequestView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Ссылка для сброса пароля отправлена на вашу почту."})

class PasswordResetConfirmView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request, *args, **kwargs):
        request.data['uid'] = request.query_params.get('uid')
        request.data['token'] = request.query_params.get('token')

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Пароль успешно сброшен."})




