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

class CenterViewSet(viewsets.ModelViewSet):
    queryset = Center.objects.all()
    serializer_class = CenterSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Allow searching by name, location, description
    search_fields = ['name', 'location', 'description']
    
    # Allow filtering by description, latitude, longitude, and related section ID
    filterset_fields = ['description', 'latitude', 'longitude', 'sections__id']

    # Allow ordering by fields
    ordering_fields = ['name', 'location', 'latitude', 'longitude']


class SectionViewSet(viewsets.ModelViewSet):
    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    filterset_fields = ['category', 'centers']

    ordering_fields = ['name', 'category', 'description']

class SectionCategoryViewSet(viewsets.ModelViewSet):
    queryset = SectionCategory.objects.all()
    serializer_class = SectionCategorySerializer
    pagination_class = StandardResultsSetPagination

class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Filter by user, section, type, and active status
    filterset_fields = ['section', 'type', 'is_active']
    search_fields = ['section__name', 'user__email']
    ordering_fields = ['start_date', 'end_date']

    def perform_create(self, serializer):
        # Automatically set the user from the JWT token (request.user)
        serializer.save(user=self.request.user)

class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Filter by center, section, status, date, start time, end time, and users (via records)
    filterset_fields = ['center', 'section', 'status', 'date', 'start_time', 'end_time', 'records__user__id']

    # Search by center name and section name
    search_fields = ['center__name', 'section__name']

    # Allow ordering by start time, end time, capacity, and reserved seats
    ordering_fields = ['start_time', 'end_time', 'capacity', 'reserved']


class RecordViewSet(viewsets.ModelViewSet):
    queryset = Record.objects.all()
    serializer_class = RecordSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user', 'section', 'schedule', 'attended']
    search_fields = ['schedule__section__name', 'user__email']
    ordering_fields = ['schedule__start_time', 'attended']

    def create(self, request, *args, **kwargs):
        user = request.user
        schedule_id = request.data.get('schedule')
        section_id = request.data.get('section')

        # Validate the section and schedule
        schedule = Schedule.objects.get(id=schedule_id)
        subscription = Subscription.objects.filter(user=user, section_id=section_id).first()

        if not subscription:
            return Response({'error': 'You do not have a valid subscription for this section.'}, status=status.HTTP_400_BAD_REQUEST)

        if subscription.section.id != schedule.section.id:
            return Response({'error': 'Subscription section does not match schedule section.'}, status=status.HTTP_400_BAD_REQUEST)

        # Combine schedule date and start_time into a datetime object
        schedule_start_datetime = datetime.combine(schedule.date, schedule.start_time)

        # Check if user has overlapping records within 1 hour
        overlapping_records = Record.objects.filter(
            user=user,
            schedule__date=schedule.date,
            schedule__start_time__range=(
                (schedule_start_datetime - timedelta(hours=1)).time(),
                (schedule_start_datetime + timedelta(hours=1)).time()
            )
        )

        if overlapping_records.exists():
            return Response({'error': 'You cannot apply for overlapping schedules within 1 hour.'}, status=status.HTTP_400_BAD_REQUEST)

        # Prevent applying to the same schedule more than once
        if Record.objects.filter(user=user, schedule=schedule).exists():
            return Response({'error': 'You have already applied for this schedule.'}, status=status.HTTP_400_BAD_REQUEST)

        # Create record
        record = Record.objects.create(
            user=user,
            schedule=schedule,
            section=schedule.section
        )
        schedule.reserved += 1
        schedule.save()

        serializer = self.get_serializer(record)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def confirm_attendance(self, request):
        # Get the record ID from the request body
        record_id = request.data.get('record_id')

        # Ensure record_id is provided
        if not record_id:
            return Response({'error': 'Record ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Retrieve the record and schedule associated with the record
            record = Record.objects.get(id=record_id, user=request.user)
            schedule = record.schedule
        except Record.DoesNotExist:
            return Response({'error': 'Record not found or you do not have access to this record.'}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user has already attended the lesson
        if record.attended:
            return Response({'error': 'You have already attended this lesson.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the time of the lesson has not arrived yet
        current_datetime = timezone.now()
        schedule_datetime = timezone.make_aware(
            timezone.datetime.combine(schedule.date, schedule.start_time)
        )

        if current_datetime < schedule_datetime:
            return Response({'error': 'The lesson has not started yet.'}, status=status.HTTP_400_BAD_REQUEST)

        # Mark the attendance
        record.attended = True
        record.save()

        return Response({'message': 'Attendance confirmed successfully.'}, status=status.HTTP_200_OK)

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