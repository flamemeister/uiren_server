from rest_framework import serializers
from .models import Center, Section, Subscription, Enrollment, Feedback, SectionCategory

class CenterSerializer(serializers.ModelSerializer):
    sections = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Center
        fields = ['id', 'name', 'description', 'location', 'sections']

class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ['id', 'center', 'name', 'category', 'schedule', 'available_times']

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['id', 'user', 'center', 'section', 'type', 'name']

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
        # Ensure no more than 3 enrollments per subscription per day
        enrollments_on_same_day = Enrollment.objects.filter(
            subscription=data['subscription'],
            time__date=data['time'].date()
        ).count()
        if enrollments_on_same_day >= 3:
            raise serializers.ValidationError('You cannot have more than 3 enrollments per subscription per day.')

        # Ensure no overlapping times
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
