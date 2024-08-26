from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Center, Section, Subscription, Enrollment, Feedback, SectionCategory
from .serializers import CenterSerializer, SectionSerializer, SubscriptionSerializer, EnrollmentSerializer, FeedbackSerializer, SectionCategorySerializer
import json
from user.models import CustomUser


class CenterViewSet(viewsets.ModelViewSet):
    queryset = Center.objects.all()
    serializer_class = CenterSerializer

class SectionCategoryViewSet(viewsets.ModelViewSet):
    queryset = SectionCategory.objects.all()
    serializer_class = SectionCategorySerializer

class SectionViewSet(viewsets.ModelViewSet):
    queryset = Section.objects.all()
    serializer_class = SectionSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category__name=category)
        return queryset


class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer

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

from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Center, Enrollment, Subscription

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

from django.shortcuts import redirect
from django.utils import timezone
from .models import Payment
import uuid
from django.views.decorators.csrf import csrf_exempt
import json

from django.http import JsonResponse

@csrf_exempt
def initiate_payment(request):
    if request.method == 'POST':
        try:
            # Чтение и парсинг тела запроса как JSON
            data = json.loads(request.body)
            student_id = data.get('student_id')
            center_id = data.get('center_id')
            section_id = data.get('section_id')
            payment_period = data.get('payment_period')
            amount = data.get('amount')
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        # Отладочный вывод для проверки
        print(f"Received amount: {amount}, type: {type(amount)}")

        if not amount:
            return JsonResponse({'error': 'Amount is required'}, status=400)
        
        try:
            amount = float(amount)
        except ValueError:
            return JsonResponse({'error': 'Invalid amount format'}, status=400)

        txn_id = str(uuid.uuid4())
        payment = Payment.objects.create(
            txn_id=txn_id,
            student_id=student_id,
            center_id=center_id,
            section_id=section_id,
            payment_period=payment_period,
            amount=amount,
            status='pending'
        )

        # Редирект на Kaspi.kz
        # Формирование URL для редиректа
        kaspi_url = f"https://kaspi.kz/pay/_gate?action=service_with_subservice&service_id=3025&subservice_id=15078&region_id=18&txn_id={txn_id}&amount={amount}&center_id={center_id}&student_id={student_id}"
        
        # Логирование URL для проверки
        print(f"Redirecting to: {kaspi_url}")

        # Редирект
        return redirect(kaspi_url)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

    return JsonResponse({'error': 'Invalid request method'}, status=405)




from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import Payment

def handle_kaspi_response(request):
    # Получение данных от Kaspi.kz
    txn_id = request.GET.get('txn_id')
    prv_txn_id = request.GET.get('prv_txn_id')
    result = request.GET.get('result')
    amount = request.GET.get('amount')

    # Обновление статуса платежа в базе данных
    payment = get_object_or_404(Payment, txn_id=txn_id)

    if result == '0':  # Успешная оплата
        payment.status = 'completed'
    else:
        payment.status = 'failed'
    
    payment.save()

    return JsonResponse({'message': 'Payment status updated successfully'})

import requests

def check_account_status(account_id):
    # Формирование запроса для проверки состояния пользователя
    kaspi_url = f"https://example.com/payment_app.cgi?command=check&account={account_id}&sum=0.00"
    
    response = requests.get(kaspi_url)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('result') == '0':
            return True  # Аккаунт доступен для пополнения
    return False  # Аккаунт не найден или недоступен











