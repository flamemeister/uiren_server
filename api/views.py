from rest_framework import viewsets, status, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from .models import Center, Section, Subscription, Schedule, Record, SectionCategory, Feedback
from .serializers import CenterSerializer, SectionSerializer, SubscriptionSerializer, ScheduleSerializer, RecordSerializer, SectionCategorySerializer, FeedbackSerializer
from .pagination import StandardResultsSetPagination
from django.utils import timezone
from datetime import timedelta, datetime
from rest_framework.exceptions import ValidationError

class CenterViewSet(viewsets.ModelViewSet):
    queryset = Center.objects.all()
    serializer_class = CenterSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    search_fields = ['name', 'location', 'description']
    filterset_fields = ['description', 'latitude', 'longitude', 'sections__id', 'users']
    ordering_fields = ['name', 'location', 'latitude', 'longitude']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        new_param = self.request.query_params.get('new', None)
        if new_param is not None:
            try:
                new_param = int(new_param)
                if new_param <= 0:
                    raise ValidationError('The "new" parameter must be a positive integer.')
                queryset = queryset.order_by('-id')[:new_param]
            except ValueError:
                raise ValidationError('The "new" parameter must be an integer.')
        return queryset

class SectionViewSet(viewsets.ModelViewSet):
    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    search_fields = ['name', 'description']
    filterset_fields = ['category', 'center']
    ordering_fields = ['name', 'category', 'description']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        new_param = self.request.query_params.get('new', None)
        if new_param is not None:
            try:
                new_param = int(new_param)
                if new_param <= 0:
                    raise ValidationError('The "new" parameter must be a positive integer.')
                queryset = queryset.order_by('-id')[:new_param]
            except ValueError:
                raise ValidationError('The "new" parameter must be an integer.')
        return queryset

class SectionCategoryViewSet(viewsets.ModelViewSet):
    queryset = SectionCategory.objects.all()
    serializer_class = SectionCategorySerializer
    pagination_class = StandardResultsSetPagination

class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['type', 'is_active']
    ordering_fields = ['start_date', 'end_date']

    def get_queryset(self):
        queryset = Subscription.objects.filter(user=self.request.user)
        current_datetime = timezone.now()
        queryset.filter(end_date__lt=current_datetime).update(is_active=False)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)  # Allow PATCH (partial update)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def perform_update(self, serializer):
        instance = serializer.save()
        # Update is_active based on end_date
        if instance.end_date < timezone.now():
            instance.is_active = False
            instance.save()

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def unactivated_subscriptions(self, request):
        # Return all unactivated subscriptions
        unactivated_subs = Subscription.objects.filter(is_activated_by_admin=False)
        serializer = self.get_serializer(unactivated_subs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def activate_subscription(self, request, pk=None):
        try:
            subscription = Subscription.objects.get(pk=pk)
        except Subscription.DoesNotExist:
            return Response({'error': 'Subscription does not exist.'}, status=status.HTTP_404_NOT_FOUND)

        subscription.is_activated_by_admin = True
        subscription.save()

        return Response({'message': 'Subscription activated successfully.'}, status=status.HTTP_200_OK)


class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = ['section', 'status', 'date', 'start_time', 'end_time', 'records__user__id', 'section__center']
    search_fields = ['section__name', 'section__center__name']
    ordering_fields = ['start_time', 'end_time', 'capacity', 'reserved']

class RecordViewSet(viewsets.ModelViewSet):
    queryset = Record.objects.all()
    serializer_class = RecordSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user', 'schedule', 'attended', 'subscription']
    search_fields = ['schedule__section__name', 'user__email']
    ordering_fields = ['schedule__start_time', 'attended']

    def get_queryset(self):
        return Record.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        user = request.user
        schedule_id = request.data.get('schedule')
        subscription_id = request.data.get('subscription')

        try:
            schedule = Schedule.objects.get(id=schedule_id)
        except Schedule.DoesNotExist:
            return Response({'error': 'Schedule does not exist.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            subscription = Subscription.objects.get(id=subscription_id, user=user, is_active=True)
        except Subscription.DoesNotExist:
            return Response({'error': 'You do not have a valid subscription.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the subscription has been activated by the admin
        if not subscription.is_activated_by_admin:
            return Response({'error': 'Your subscription has not been activated by an admin.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check subscription expiry
        current_datetime = timezone.now()
        if subscription.end_date < current_datetime:
            return Response({'error': 'Your subscription has expired.'}, status=status.HTTP_400_BAD_REQUEST)

        # Prevent multiple reservations for overlapping schedules
        schedule_start_datetime = datetime.combine(schedule.date, schedule.start_time)
        overlapping_records = Record.objects.filter(
            user=user,
            subscription=subscription,
            schedule__date=schedule.date,
            schedule__start_time__range=(
                (schedule_start_datetime - timedelta(hours=1)).time(),
                (schedule_start_datetime + timedelta(hours=1)).time()
            )
        )

        if overlapping_records.exists():
            return Response({'error': 'You cannot apply for overlapping schedules using the same subscription.'}, status=status.HTTP_400_BAD_REQUEST)

        if Record.objects.filter(user=user, schedule=schedule, subscription=subscription).exists():
            return Response({'error': 'You have already applied for this schedule with this subscription.'}, status=status.HTTP_400_BAD_REQUEST)

        record = Record.objects.create(
            user=user,
            schedule=schedule,
            subscription=subscription
        )
        schedule.reserved += 1
        schedule.save()

        serializer = self.get_serializer(record)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def unconfirmed_records(self, request):
        section_id = request.query_params.get('section_id')
        if not section_id:
            return Response({'error': 'Section ID is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            section = Section.objects.get(id=section_id)
        except Section.DoesNotExist:
            return Response({'error': 'Section not found.'}, status=status.HTTP_404_NOT_FOUND)
        records = Record.objects.filter(user=request.user, schedule__section=section, attended=False)
        serializer = self.get_serializer(records, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def confirm_attendance(self, request):
        record_id = request.data.get('record_id')
        if not record_id:
            return Response({'error': 'Record ID is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            record = Record.objects.get(id=record_id, user=request.user)
        except Record.DoesNotExist:
            return Response({'error': 'Record not found or you do not have access to this record.'}, status=status.HTTP_404_NOT_FOUND)
        if record.attended:
            return Response({'error': 'You have already attended this lesson.'}, status=status.HTTP_400_BAD_REQUEST)
        record.attended = True
        record.save()
        return Response({'message': 'Attendance confirmed successfully.'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_records(self, request):
        record_type = request.query_params.get('type', 'all')  # 'past', 'current', 'future', 'all'
        current_datetime = timezone.now()
        records = self.get_queryset()

        if record_type == 'past':
            records = records.filter(schedule__date__lt=current_datetime.date())
        elif record_type == 'current':
            records = records.filter(schedule__date=current_datetime.date())
        elif record_type == 'future':
            records = records.filter(schedule__date__gt=current_datetime.date())

        records = records.order_by('schedule__date', 'schedule__start_time')

        page = self.paginate_queryset(records)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(records, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    permission_classes = [IsAuthenticated]  

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        user_feedback_only = self.request.query_params.get('user_feedback_only', None)
        if user_feedback_only:
            return Feedback.objects.filter(user=self.request.user)
        return super().get_queryset()

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count
from datetime import timedelta
from user.models import CustomUser
from api.models import Subscription
from api.models import Center
from api.models import Schedule

@api_view(['GET'])
def dashboard_metrics(request):
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    
    # Total Users
    total_users = CustomUser.objects.count()

    # Active Subscriptions
    active_subscriptions = Subscription.objects.filter(is_active=True).count()

    # Total Centers
    total_centers = Center.objects.count()

    # Lessons Today or This Week
    lessons_today = Schedule.objects.filter(date=today).count()
    lessons_this_week = Schedule.objects.filter(date__gte=start_of_week, date__lte=today + timedelta(days=6)).count()

    # Feedback Count (if applicable)
    feedback_count = Feedback.objects.count()

    return Response({
        'total_users': total_users,
        'active_subscriptions': active_subscriptions,
        'total_centers': total_centers,
        'lessons_today': lessons_today,
        'lessons_this_week': lessons_this_week,
        'feedback_count': feedback_count,
    })

from rest_framework.decorators import api_view
from rest_framework.response import Response
from user.models import CustomUser
from api.models import Subscription
from api.models import Feedback, Record
from django.utils import timezone

@api_view(['GET'])
def recent_activities(request):
    # Recent User Signups
    recent_signups = CustomUser.objects.order_by('-date_joined')[:5]

    # Recent Feedback
    recent_feedback = Feedback.objects.order_by('-created_at')[:5]

    # Recent Lesson Enrollments
    recent_enrollments = Record.objects.order_by('-id')[:5]

    return Response({
        'recent_signups': [{
            'email': signup.email,
            'date_joined': signup.date_joined
        } for signup in recent_signups],
        'recent_feedback': [{
            'user': feedback.user.email,
            'center': feedback.center.name,
            'stars': feedback.stars,
            'text': feedback.text,
            'created_at': feedback.created_at,
        } for feedback in recent_feedback],
        'recent_enrollments': [{
            'user': enrollment.user.email,
            'section': enrollment.section.name,
            'center': enrollment.schedule.center.name,
            'date': enrollment.schedule.date,
            'attended': enrollment.attended,
        } for enrollment in recent_enrollments],
    })

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from api.models import Subscription
from api.models import Schedule
from datetime import timedelta

@api_view(['GET'])
def dashboard_notifications(request):
    today = timezone.now().date()

    # Upcoming Lessons within the next 7 days
    upcoming_lessons = Schedule.objects.filter(date__gte=today, date__lte=today + timedelta(days=7))

    # Expired Subscriptions
    expired_subscriptions = Subscription.objects.filter(end_date__lt=today, is_active=False)

    return Response({
        'upcoming_lessons': [{
            'center': lesson.center.name,
            'section': lesson.section.name,
            'date': lesson.date,
            'start_time': lesson.start_time,
            'end_time': lesson.end_time,
            'capacity': lesson.capacity,
            'reserved': lesson.reserved,
        } for lesson in upcoming_lessons],
        'expired_subscriptions': [{
            'user': subscription.user.email,
            'section': subscription.section.name,
            'end_date': subscription.end_date,
        } for subscription in expired_subscriptions]
    })