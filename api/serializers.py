from rest_framework import serializers
from .models import Center, Section, Subscription, Schedule, Record, SectionCategory, Feedback
from user.models import CustomUser
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
    weekly_pattern = serializers.JSONField()

    class Meta:
        model = Section
        fields = ['id', 'name', 'category', 'image', 'center', 'description', 'qr_code', 'weekly_pattern']

    def create(self, validated_data):
        weekly_pattern = validated_data.pop('weekly_pattern', None)

        section = Section.objects.create(**validated_data)

        if weekly_pattern:
            section.weekly_pattern = weekly_pattern
            section.save()

        self._generate_schedules_for_next_month(section, weekly_pattern)
        return section

    def _generate_schedules_for_next_month(self, section, weekly_pattern):
        today = timezone.now().date()
        first_day_of_next_month = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
        last_day_of_next_month = first_day_of_next_month.replace(
            day=calendar.monthrange(first_day_of_next_month.year, first_day_of_next_month.month)[1])

        day_mapping = {
            'Понедельник': 'Monday',
            'Вторник': 'Tuesday',
            'Среда': 'Wednesday',
            'Четверг': 'Thursday',
            'Пятница': 'Friday',
            'Суббота': 'Saturday',
            'Воскресенье': 'Sunday'
        }

        current_date = first_day_of_next_month
        while current_date <= last_day_of_next_month:
            day_name = current_date.strftime('%A')  
            for pattern in weekly_pattern:
                if day_mapping.get(pattern['day']) == day_name:
                    for interval in pattern['intervals']:
                        start_time = interval.get('start_time')
                        end_time = interval.get('end_time')
                        
                        if start_time and end_time:
                            Schedule.objects.create(
                                section=section,
                                date=current_date,
                                start_time=start_time,
                                end_time=end_time,
                                capacity=20,  
                            )
            current_date += timedelta(days=1)

    def update(self, instance, validated_data):
        weekly_pattern = validated_data.pop('weekly_pattern', None)
        section = super().update(instance, validated_data)

        if weekly_pattern:
            section.weekly_pattern = weekly_pattern
            section.save()

            section.schedules.all().delete()
            self._generate_schedules_for_next_month(section, weekly_pattern)

        return section

class SubscriptionSerializer(serializers.ModelSerializer):
    freeze_days = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Subscription
        fields = ['id', 'name', 'user', 'type', 'start_date', 'end_date', 'is_active', 'is_activated_by_admin', 'is_frozen', 'frozen_start_date', 'frozen_end_date', 'freeze_days']
        read_only_fields = ['user', 'start_date', 'end_date', 'is_active', 'is_frozen', 'frozen_start_date', 'frozen_end_date']

    def update(self, instance, validated_data):
        freeze_days = validated_data.pop('freeze_days', None)
        if freeze_days:
            instance.freeze(freeze_days)
        return super().update(instance, validated_data)

class ScheduleSerializer(serializers.ModelSerializer):
    weekly_pattern = serializers.JSONField(write_only=True, required=False)

    class Meta:
        model = Schedule
        fields = ['id', 'section', 'date', 'start_time', 'end_time', 'capacity', 'reserved', 'status', 'weekly_pattern']

    def to_internal_value(self, data):
        if 'weekly_pattern' in data:
            self.fields['date'].required = False
            self.fields['start_time'].required = False
            self.fields['end_time'].required = False
            self.fields['capacity'].required = False
        return super().to_internal_value(data)

    def create(self, validated_data):
        weekly_pattern = validated_data.pop('weekly_pattern', None)
        
        if weekly_pattern:
            self._generate_schedules_for_next_month(validated_data['section'], weekly_pattern)
            return Schedule.objects.filter(section=validated_data['section']).order_by('-id').first()
        
        return super().create(validated_data)

    def _generate_schedules_for_next_month(self, section, weekly_pattern):
        today = timezone.now().date()
        end_date = today + timedelta(days=30)

        day_mapping = {
            'Понедельник': 'Monday',
            'Вторник': 'Tuesday',
            'Среда': 'Wednesday',
            'Четверг': 'Thursday',
            'Пятница': 'Friday',
            'Суббота': 'Saturday',
            'Воскресенье': 'Sunday'
        }

        current_date = today
        while current_date <= end_date:
            day_name = current_date.strftime('%A')
            for pattern in weekly_pattern:
                if day_mapping.get(pattern['day']) == day_name:
                    for interval in pattern['intervals']:
                        start_time = interval.get('start_time')
                        end_time = interval.get('end_time')
                        capacity = interval.get('capacity', 20)

                        if start_time and end_time:
                            Schedule.objects.create(
                                section=section,
                                date=current_date,
                                start_time=start_time,
                                end_time=end_time,
                                capacity=capacity,
                            )
            current_date += timedelta(days=1)

class RecordSerializer(serializers.ModelSerializer):
    schedule = ScheduleSerializer(read_only=True)
    subscription = SubscriptionSerializer(read_only=True)

    class Meta:
        model = Record
        fields = ['id', 'user', 'schedule', 'attended', 'subscription', 'is_canceled']
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