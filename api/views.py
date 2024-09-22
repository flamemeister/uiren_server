from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.utils import timezone
from .models import Center, Section, Subscription, Enrollment, Feedback, SectionCategory
from .serializers import CenterSerializer, SectionSerializer, SubscriptionSerializer, EnrollmentSerializer, FeedbackSerializer, SectionCategorySerializer
import json
from user.models import CustomUser
from django.shortcuts import redirect, get_object_or_404
import uuid
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import requests
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from .pagination import CenterPagination  

from rest_framework import viewsets, status, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Center, Section, SectionCategory
from .serializers import CenterSerializer, SectionSerializer
from rest_framework.response import Response

class CenterViewSet(viewsets.ModelViewSet):
    queryset = Center.objects.all()
    serializer_class = CenterSerializer
    pagination_class = CenterPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['sections__id']
    search_fields = ['name', 'sections__name']
    ordering_fields = ['name', 'location']

    def get_queryset(self):
        queryset = super().get_queryset()
        section_ids = self.request.query_params.getlist('section', None)
        category_ids = self.request.query_params.getlist('category', None)

        # Filter by sections
        if section_ids:
            queryset = queryset.filter(sections__id__in=section_ids)

        # Filter by categories through sections
        if category_ids:
            queryset = queryset.filter(sections__category__id__in=category_ids)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'results': serializer.data,
            'next': None,
            'previous': None
        })

class SectionViewSet(viewsets.ModelViewSet):
    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    pagination_class = CenterPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name']
    filterset_fields = ['category__id']

    def get_queryset(self):
        queryset = super().get_queryset()
        category_ids = self.request.query_params.getlist('category', None)
        if category_ids:
            queryset = queryset.filter(category__id__in=category_ids)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'results': serializer.data,
            'next': None,
            'previous': None
        })

class SectionCategoryViewSet(viewsets.ModelViewSet):
    queryset = SectionCategory.objects.all()
    serializer_class = SectionCategorySerializer
    pagination_class = CenterPagination  # Use the same pagination class

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # Apply pagination if 'page' parameter is present
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)  # Serialize the paginated data
            return self.get_paginated_response(serializer.data)

        # When no pagination is applied, return all results in 'results' key
        serializer = self.get_serializer(queryset, many=True)  # Serialize all data
        return Response({
            'count': queryset.count(),
            'results': serializer.data,  # Always return serialized data
            'next': None,
            'previous': None
        })


class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    # permission_classes = [IsAuthenticated]  # Любой аутентифицированный пользователь может покупать абонементы

    def create(self, request, *args, **kwargs):
        data = request.data
        buyer = request.user  

        child_id = data.get('user')
        try:
            if child_id:
                child = CustomUser.objects.get(id=child_id)
            else:
                child = buyer
        except CustomUser.DoesNotExist:
            return Response({'error': 'Child not found.'}, status=status.HTTP_400_BAD_REQUEST)

        section_id = data.get('section')
        section = None
        if section_id:
            try:
                section = Section.objects.get(id=section_id)
            except Section.DoesNotExist:
                return Response({'error': 'Section not found.'}, status=status.HTTP_400_BAD_REQUEST)

        subscription = Subscription.objects.create(
            purchased_by=buyer,
            user=child,
            section=section,
            type=data.get('type'),
            name=data.get('name'),
            expiration_date=timezone.now() + timezone.timedelta(days=30)  # Пример срока действия
        )

        serializer = self.get_serializer(subscription)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='deactivate', permission_classes=[IsAuthenticated])
    def deactivate_subscription(self, request, pk=None):
        subscription = self.get_object()
        if subscription.purchased_by != request.user:
            return Response({'error': 'You do not have permission to deactivate this subscription.'}, status=status.HTTP_403_FORBIDDEN)
        subscription.is_active = False
        subscription.save()
        return Response({'status': 'Subscription deactivated.'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def my_subscriptions(self, request):
        iin = request.query_params.get('iin')
        if not iin:
            return Response({"error": "IIN is required"}, status=status.HTTP_400_BAD_REQUEST)
        subscriptions = Subscription.objects.filter(user__iin=iin)
        serializer = self.get_serializer(subscriptions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def rename(self, request, pk=None):
        subscription = self.get_object()
        if subscription.user != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        new_name = request.data.get('name')
        subscription.name = new_name
        subscription.save()
        return Response(status=status.HTTP_200_OK)

class EnrollmentViewSet(viewsets.ModelViewSet):
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer

    @action(detail=False, methods=['get'])
    def my_enrollments(self, request):
        user = request.user
        enrollments = Enrollment.objects.filter(user=user)
        serializer = self.get_serializer(enrollments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        enrollment = self.get_object()
        if enrollment.user != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        enrollment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        enrollment = self.get_object()
        if enrollment.user != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        enrollment.confirmed = True
        enrollment.confirmation_time = timezone.now()
        enrollment.save()
        return Response(status=status.HTTP_200_OK)

class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer

@api_view(['POST'])
def confirm_attendance(request):
    if not request.user.is_authenticated:
        return Response({'error': 'Authentication credentials were not provided'}, status=status.HTTP_401_UNAUTHORIZED)

    qr_code_data = request.data.get('qr_code', None)
    if qr_code_data is None:
        return Response({'error': 'QR code data not provided'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        data = json.loads(qr_code_data)
        center_id = data.get('center_id')
        center = get_object_or_404(Center, id=center_id)
        user = request.user
    except (json.JSONDecodeError, KeyError) as e:
        return Response({'error': f'Invalid QR code data: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

    if 'subscriptions' not in data:
        return Response({'error': 'No subscriptions data found in the QR code'}, status=status.HTTP_400_BAD_REQUEST)
    
    subscriptions = Subscription.objects.filter(
        user=user,
        center=center,
        id__in=[s['subscription_id'] for s in data['subscriptions']]
    )
    if not subscriptions.exists():
        return Response({'error': 'No active subscription found for this center'}, status=status.HTTP_400_BAD_REQUEST)

    enrollment = Enrollment.objects.filter(
        user=user,
        section__center=center,
        confirmed=False,
        subscription__in=subscriptions
    ).first()
    if not enrollment:
        return Response({'error': 'No active enrollment found for this center'}, status=status.HTTP_400_BAD_REQUEST)

    enrollment.confirmed = True
    enrollment.confirmation_time = timezone.now()
    enrollment.save()

    return Response({'message': 'Attendance confirmed successfully'}, status=status.HTTP_200_OK)

MANAGER_WHATSAPP_NUMBER = '+77073478844'


@api_view(['GET'])
def redirect_to_whatsapp(request):
    """Endpoint to redirect to WhatsApp chat with the manager for payment."""
    message = "Hello, I would like to make a payment."
    whatsapp_url = f"https://wa.me/{MANAGER_WHATSAPP_NUMBER}?text={message}"
    
    return redirect(whatsapp_url)


