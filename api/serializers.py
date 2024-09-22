from rest_framework import serializers
from .models import Center, Section, Subscription, Enrollment, Feedback, SectionCategory, Schedule
from user.models import CustomUser
from django.utils import timezone

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
    image = serializers.ImageField(required=False, allow_null=True)  

    class Meta:
        model = Section
        fields = ['id', 'name', 'category', 'schedules', 'image']


from django.utils import timezone
from rest_framework import serializers
from .models import Subscription, CustomUser

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = [
            'id', 'purchased_by', 'user', 'section', 
            'type', 'name', 'activation_date', 'expiration_date', 'is_active'
        ]
        # Поле expiration_date делаем только для чтения, чтобы оно не передавалось в запросе
        read_only_fields = ['purchased_by', 'activation_date', 'expiration_date', 'is_active']

    def create(self, validated_data):
        request_user = self.context['request'].user

        if not request_user.is_authenticated or isinstance(request_user, CustomUser) is False:
            raise serializers.ValidationError("User must be authenticated.")

        # Если IIN присутствует, ищем пользователя по IIN
        user_data = validated_data.pop('user', {})
        iin = user_data.get('iin', None)

        if iin:
            user = CustomUser.objects.get(iin=iin)
        else:
            user = request_user

        # Получаем тип подписки и вычисляем expiration_date
        subscription_type = validated_data.get('type')

        # Отладочный вывод для проверки корректности логики
        print(f"Создаем подписку для типа: {subscription_type}")

        # Логика для расчета даты истечения в зависимости от типа подписки
        if subscription_type == 1:
            expiration_date = timezone.now() + timezone.timedelta(days=30)  # 1 месяц
        elif subscription_type == 2:
            expiration_date = timezone.now() + timezone.timedelta(days=180)  # 6 месяцев
        elif subscription_type == 3:
            expiration_date = timezone.now() + timezone.timedelta(days=365)  # 12 месяцев
        else:
            expiration_date = timezone.now() + timezone.timedelta(days=30)  # По умолчанию 1 месяц

        # Добавляем еще один вывод для проверки даты истечения
        print(f"Дата истечения: {expiration_date}")

        # Создаем объект подписки с рассчитанной датой expiration_date
        subscription = Subscription.objects.create(
            purchased_by=request_user,
            user=user,
            expiration_date=expiration_date,  # Устанавливаем рассчитанную дату
            **validated_data
        )

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
