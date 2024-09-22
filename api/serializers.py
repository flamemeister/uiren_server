from rest_framework import serializers
from .models import Center, Section, Subscription, Schedule, Record, SectionCategory

class CenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Center
        fields = ['id', 'name', 'location', 'latitude', 'longitude', 'qr_code', 'image', 'description']

class SectionSerializer(serializers.ModelSerializer):
    centers = serializers.PrimaryKeyRelatedField(queryset=Center.objects.all(), many=True)

    class Meta:
        model = Section
        fields = ['id', 'name', 'category', 'image', 'centers', 'description']

    def create(self, validated_data):
        # Pop centers from validated data since we need to handle them separately
        centers_data = validated_data.pop('centers', [])
        
        # Create the section
        section = Section.objects.create(**validated_data)
        
        # Add the centers to the ManyToMany relationship
        section.centers.set(centers_data)
        
        return section

    def update(self, instance, validated_data):
        # Pop centers from validated data
        centers_data = validated_data.pop('centers', None)
        
        # Update other fields
        instance = super().update(instance, validated_data)
        
        # If centers are provided, update the ManyToMany relationship
        if centers_data is not None:
            instance.centers.set(centers_data)
        
        return instance

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['id', 'user', 'section', 'type', 'start_date', 'end_date', 'is_active']
        read_only_fields = ['user', 'start_date', 'end_date', 'is_active']


class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = ['id', 'section', 'center', 'date', 'start_time', 'end_time', 'capacity', 'reserved', 'status']

class RecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Record
        fields = ['id', 'user', 'schedule', 'attended', 'section']

class SectionCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SectionCategory
        fields = ['id', 'name', 'image']
