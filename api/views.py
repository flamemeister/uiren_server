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

        # Role management: If user is Staff, filter centers they are assigned to
        if self.request.user.role == 'STAFF':
            queryset = queryset.filter(users=self.request.user)

        if new_param is not None:
            try:
                new_param = int(new_param)
                if new_param <= 0:
                    raise ValidationError('The "new" parameter must be a positive integer.')
                queryset = queryset.order_by('-id')[:new_param]
            except ValueError:
                raise ValidationError('The "new" parameter must be an integer.')
        return queryset

    def create(self, request, *args, **kwargs):
        if request.user.role != 'ADMIN':
            return Response({'error': 'You are not allowed to create centers.'}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def perform_update(self, serializer):
        if self.request.user.role == 'STAFF':
            center = self.get_object()
            if not center.users.filter(id=self.request.user.id).exists():
                raise ValidationError("You are not allowed to edit this center.")
        serializer.save()


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

        # Role management: If user is Staff, filter sections they are assigned to
        if self.request.user.role == 'STAFF':
            queryset = queryset.filter(center__users=self.request.user)

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

    def perform_update(self, serializer):
        if self.request.user.role == 'STAFF':
            section = self.get_object()
            if not section.center.users.filter(id=self.request.user.id).exists():
                raise ValidationError("You are not allowed to edit this section.")
        serializer.save()


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
        # Role management: Admin can view all subscriptions, others can only see their own
        if self.request.user.role == 'ADMIN':
            return Subscription.objects.all()
        return Subscription.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        # Role management: Allow users to update only their own subscriptions
        if self.request.user.role != 'ADMIN' and instance.user != self.request.user:
            return Response({'error': 'You are not allowed to update this subscription.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def perform_update(self, serializer):
        instance = serializer.save()
        if instance.end_date < timezone.now():
            instance.is_active = False
            instance.save()

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def unactivated_subscriptions(self, request):
        if self.request.user.role != 'ADMIN':
            return Response({'error': 'You are not allowed to view unactivated subscriptions.'}, status=status.HTTP_403_FORBIDDEN)
        unactivated_subs = Subscription.objects.filter(is_activated_by_admin=False)
        serializer = self.get_serializer(unactivated_subs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def activate_subscription(self, request, pk=None):
        if self.request.user.role != 'ADMIN':
            return Response({'error': 'You are not allowed to activate subscriptions.'}, status=status.HTTP_403_FORBIDDEN)
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

    def get_queryset(self):
        # Role management: Staff can view schedules for their own centers
        if self.request.user.role == 'STAFF':
            return Schedule.objects.filter(section__center__users=self.request.user)
        elif self.request.user.role == 'ADMIN':
            return Schedule.objects.all()
        return super().get_queryset()


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
        # Role management: Admin can view all records, users can only view their own
        if self.request.user.role == 'ADMIN':
            return Record.objects.all()
        return Record.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'], url_path='user-records/(?P<user_id>\d+)', permission_classes=[IsAuthenticated])
    def user_records(self, request, user_id=None):
        """
        Custom action to return all records for a specific user by user ID.
        Only Admin and Staff users can access this action.
        """
        # Check if the logged-in user is Admin or Staff
        if request.user.role not in ['ADMIN', 'STAFF']:
            return Response({'error': 'You do not have permission to access user records.'}, status=status.HTTP_403_FORBIDDEN)

        # Check if the user exists
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        # For Admin: return all records for the user
        if request.user.role == 'ADMIN':
            records = Record.objects.filter(user=user)
        
        # For Staff: return records related to sections they are assigned to
        elif request.user.role == 'STAFF':
            records = Record.objects.filter(user=user, schedule__section__center__users=request.user)
        
        # Serialize and return the records
        serializer = self.get_serializer(records, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

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

        if not subscription.is_activated_by_admin:
            return Response({'error': 'Your subscription has not been activated by an admin.'}, status=status.HTTP_400_BAD_REQUEST)

        current_datetime = timezone.now()
        if subscription.end_date < current_datetime:
            return Response({'error': 'Your subscription has expired.'}, status=status.HTTP_400_BAD_REQUEST)

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
        record_type = request.query_params.get('type', 'all')
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
    
    total_users = CustomUser.objects.count()
    active_subscriptions = Subscription.objects.filter(is_active=True).count()
    total_centers = Center.objects.count()
    lessons_today = Schedule.objects.filter(date=today).count()
    lessons_this_week = Schedule.objects.filter(date__gte=start_of_week, date__lte=today + timedelta(days=6)).count()
    feedback_count = Feedback.objects.count()

    return Response({
        'total_users': total_users,
        'active_subscriptions': active_subscriptions,
        'total_centers': total_centers,
        'lessons_today': lessons_today,
        'lessons_this_week': lessons_this_week,
        'feedback_count': feedback_count,
    })


@api_view(['GET'])
def recent_activities(request):
    recent_signups = CustomUser.objects.order_by('-date_joined')[:5]
    recent_feedback = Feedback.objects.order_by('-created_at')[:5]
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
            'section': enrollment.schedule.section.name,
            'center': enrollment.schedule.section.center.name,
            'date': enrollment.schedule.date,
            'attended': enrollment.attended,
        } for enrollment in recent_enrollments],
    })


@api_view(['GET'])
def dashboard_notifications(request):
    today = timezone.now().date()

    upcoming_lessons = Schedule.objects.filter(date__gte=today, date__lte=today + timedelta(days=7))
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
