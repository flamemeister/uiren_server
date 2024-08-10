from rest_framework import serializers
from .models import Center, Section, Subscription, Enrollment, Feedback, SectionCategory, Schedule

class CenterSerializer(serializers.ModelSerializer):
    sections = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    qr_code_url = serializers.ImageField(source='qr_code', read_only=True)

    class Meta:
        model = Center
        fields = ['id', 'name', 'description', 'location', 'sections', 'qr_code_url', 'link']

class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = ['id', 'center', 'section', 'day_of_week', 'start_time', 'end_time']

class SectionSerializer(serializers.ModelSerializer):
    schedules = ScheduleSerializer(many=True, read_only=True, source='schedules')

    class Meta:
        model = Section
        fields = ['id', 'name', 'center', 'category', 'schedules', 'available_times']

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['id', 'user', 'center', 'section', 'type', 'name', 'activation_date', 'expiration_date', 'is_active']

    def update(self, instance, validated_data):
        if 'name' in validated_data:
            instance.name = validated_data['name']
        instance.save()
        return instance

class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = ['id', 'user', 'section', 'subscription', 'time', 'confirmed', 'confirmation_time']

    def validate(self, data):
        enrollments_on_same_day = Enrollment.objects.filter(
            subscription=data['subscription'],
            time__date=data['time'].date()
        ).count()
        if enrollments_on_same_day >= 3:
            raise serializers.ValidationError('You cannot have more than 3 enrollments per subscription per day.')
        overlapping_enrollments = Enrollment.objects.filter(
            subscription=data['subscription'],
            time=data['time']
        ).exists()
        if overlapping_enrollments:
            raise serializers.ValidationError('Enrollment times cannot overlap.')

        return data

class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ['id', 'user', 'center', 'feedback']

class SectionCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SectionCategory
        fields = ['id', 'name']
