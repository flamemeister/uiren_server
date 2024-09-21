from rest_framework import serializers
from .models import Center, Section, Subscription, Enrollment, Feedback, SectionCategory, Schedule
from user.models import CustomUser

class CenterSerializer(serializers.ModelSerializer):
    sections = serializers.PrimaryKeyRelatedField(queryset=Section.objects.all(), many=True)
    image = serializers.ImageField(required=False, allow_null=True)  # Добавляем поле для изображения

    class Meta:
        model = Center
        fields = ['id', 'name', 'description', 'location', 'latitude', 'longitude', 'sections', 'link', 'image']

    def create(self, validated_data):
        sections = validated_data.pop('sections', [])
        center = Center.objects.create(**validated_data)
        center.sections.set(sections)
        return center

    def update(self, instance, validated_data):
        sections = validated_data.pop('sections', None)
        instance = super().update(instance, validated_data)
        if sections is not None:
            instance.sections.set(sections)
        return instance


class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = ['id', 'center', 'section', 'day_of_week', 'start_time', 'end_time']

class SectionSerializer(serializers.ModelSerializer):
    schedules = ScheduleSerializer(many=True, read_only=True)
    image = serializers.ImageField(required=False, allow_null=True)  # Добавляем поле для изображения

    class Meta:
        model = Section
        fields = ['id', 'name', 'category', 'schedules', 'image']


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = [
            'id', 'purchased_by', 'user', 'section', 
            'type', 'name', 'activation_date', 'expiration_date', 'is_active'
        ]
        read_only_fields = ['purchased_by', 'activation_date', 'is_active']

    def create(self, validated_data):
        user_data = validated_data.pop('user', {})
        iin = user_data.get('iin')
        if iin:
            user = CustomUser.objects.get(iin=iin)
        else:
            user = self.context['request'].user
        subscription = Subscription.objects.create(user=user, **validated_data)
        return subscription

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
        fields = ['id', 'name', 'image']
