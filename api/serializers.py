from rest_framework import serializers
from .models import Center, Section, Subscription, Schedule, Record, SectionCategory, Feedback
from user.models import CustomUser  # Assuming this exists
from datetime import timedelta
import calendar
from django.utils import timezone


class CenterSerializer(serializers.ModelSerializer):
    users = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all(), many=True, required=False)

    class Meta:
        model = Center
        fields = ['id', 'name', 'location', 'latitude', 'longitude', 'image', 'description', 'about', 'users']

class SectionSerializer(serializers.ModelSerializer):
    center = serializers.PrimaryKeyRelatedField(queryset=Center.objects.all())
    qr_code = serializers.ImageField(read_only=True)
    weekly_pattern = serializers.JSONField()  # Allow posting weekly pattern

    class Meta:
        model = Section
        fields = ['id', 'name', 'category', 'image', 'center', 'description', 'qr_code', 'weekly_pattern']

    def create(self, validated_data):
        # Extract the weekly pattern from the validated data
        weekly_pattern = validated_data.pop('weekly_pattern')

        # Create the section
        section = Section.objects.create(weekly_pattern=weekly_pattern, **validated_data)

        # Generate schedules for the next month
        self._generate_schedules_for_next_month(section, weekly_pattern)

        return section

    def _generate_schedules_for_next_month(self, section, weekly_pattern):
        """
        Helper function to generate schedules for the next month based on the weekly pattern.
        """
        today = timezone.now().date()
        first_day_of_next_month = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
        last_day_of_next_month = first_day_of_next_month.replace(day=calendar.monthrange(first_day_of_next_month.year, first_day_of_next_month.month)[1])

        # Loop over each day in the next month and apply the weekly pattern
        current_date = first_day_of_next_month
        while current_date <= last_day_of_next_month:
            day_name = current_date.strftime('%A')  # Get the day name (e.g., Monday, Tuesday)

            for pattern in weekly_pattern:
                if pattern['day'] == day_name:
                    start_time = pattern['start_time']
                    end_time = pattern['end_time']

                    # Create a new schedule for this day
                    Schedule.objects.create(
                        section=section,
                        date=current_date,
                        start_time=start_time,
                        end_time=end_time,
                        capacity=20,  # Default capacity, can be customized
                    )

            # Move to the next day
            current_date += timedelta(days=1)


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['id', 'name', 'user', 'type', 'start_date', 'end_date', 'is_active']
        read_only_fields = ['user', 'start_date', 'end_date', 'is_active']

class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = ['id', 'section', 'date', 'start_time', 'end_time', 'capacity', 'reserved', 'status']

class RecordSerializer(serializers.ModelSerializer):
    schedule = ScheduleSerializer(read_only=True)
    subscription = SubscriptionSerializer(read_only=True)

    class Meta:
        model = Record
        fields = ['id', 'user', 'schedule', 'attended', 'subscription']
        read_only_fields = ['user', 'attended', 'subscription']

class SectionCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SectionCategory
        fields = ['id', 'name', 'image']

class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ['id', 'user', 'text', 'stars', 'center', 'created_at']
        read_only_fields = ['user', 'created_at']
