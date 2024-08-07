from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from .models import Center, Enrollment, Subscription
from django.utils import timezone

class QRCodeAttendanceTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.center = Center.objects.create(name='Test Center', description='Test Description', location='Test Location')

        self.subscription = Subscription.objects.create(user=self.user, center=self.center, type='8 уроков', name='Test Subscription')
        self.enrollment = Enrollment.objects.create(user=self.user, section=None, subscription=self.subscription, time=timezone.now())

    def test_confirm_attendance_success(self):
        self.client.login(username='testuser', password='testpass')
        url = reverse('confirm_attendance')
        data = {'qr_code': str(self.center.id)}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Attendance confirmed successfully')

    def test_confirm_attendance_no_qr_code(self):
        self.client.login(username='testuser', password='testpass')
        url = reverse('confirm_attendance')
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'QR code data not provided')

    def test_confirm_attendance_no_enrollment(self):
        new_center = Center.objects.create(name='New Center', description='New Description', location='New Location')
        self.client.login(username='testuser', password='testpass')
        url = reverse('confirm_attendance')
        data = {'qr_code': str(new_center.id)}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'No active subscription found for this center')
