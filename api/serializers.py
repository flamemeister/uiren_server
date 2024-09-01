from rest_framework import serializers
from .models import Center, Section, Subscription, Enrollment, Feedback, SectionCategory, Schedule
from user.models import CustomUser

class CenterSerializer(serializers.ModelSerializer):
    sections = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    qr_code_url = serializers.ImageField(source='qr_code', read_only=True)

    class Meta:
        model = Center
        fields = ['id', 'name', 'description', 'location', 'latitude', 'longitude', 'sections', 'qr_code_url', 'link']

class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = ['id', 'center', 'section', 'day_of_week', 'start_time', 'end_time']

class SectionSerializer(serializers.ModelSerializer):
    schedules = ScheduleSerializer(many=True, read_only=True)

    class Meta:
        model = Section
        fields = ['id', 'name', 'center', 'category', 'schedules', 'available_times']


class SubscriptionSerializer(serializers.ModelSerializer):
    iin = serializers.CharField(source='user.iin')
    password = serializers.CharField(source='user.password', write_only=True)  

    class Meta:
        model = Subscription
        fields = [
            'id', 'purchased_by', 'user', 'center', 'section', 
            'type', 'name', 'activation_date', 'expiration_date', 'is_active'
        ]
        read_only_fields = ['purchased_by', 'activation_date', 'is_active']

    def create(self, validated_data):
        iin = validated_data.pop('user')['iin']
        user = CustomUser.objects.get(iin=iin)
        subscription = Subscription.objects.create(user=user, **validated_data)
        return subscriptionce

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
