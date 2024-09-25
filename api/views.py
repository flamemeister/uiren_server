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
    
    search_fields = ['name', 'description', 'about']
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
        # Update is_active status
        queryset.filter(end_date__lt=current_datetime).update(is_active=False)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

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

        # Validate the schedule
        try:
            schedule = Schedule.objects.get(id=schedule_id)
        except Schedule.DoesNotExist:
            return Response({'error': 'Schedule does not exist.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate the subscription
        try:
            subscription = Subscription.objects.get(id=subscription_id, user=user, is_active=True)
        except Subscription.DoesNotExist:
            return Response({'error': 'You do not have a valid subscription.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check subscription validity
        current_datetime = timezone.now()
        if subscription.end_date < current_datetime:
            return Response({'error': 'Your subscription has expired.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check for overlapping records with the same subscription
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
            return Response({'error': 'You cannot apply for overlapping schedules within 1 hour using the same subscription.'}, status=status.HTTP_400_BAD_REQUEST)

        # Prevent applying to the same schedule more than once with the same subscription
        if Record.objects.filter(user=user, schedule=schedule, subscription=subscription).exists():
            return Response({'error': 'You have already applied for this schedule with this subscription.'}, status=status.HTTP_400_BAD_REQUEST)

        # Create record
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
