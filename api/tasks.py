from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from twilio.rest import Client
from user.models import CustomUser
from api.models import Schedule, Record


TWILIO_ACCOUNT_SID = 'AC8a0514493862a7c1b2357b4156b05ecb'
TWILIO_AUTH_TOKEN = '6d5022469449fdeeeca39f7adda3117e'
TWILIO_WHATSAPP_FROM = 'whatsapp:+14155238886'

# Twilio client setup
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

@shared_task
def notify_users_two_hours_before_lesson():
    """Notify users when they have a lesson they're recorded for starting in less than 2 hours."""
    now = timezone.now()
    two_hours_later = now + timedelta(hours=2)

    print(f"Now: {now}, Two Hours Later: {two_hours_later}")

    # Get all schedules starting in the next 2 hours
    upcoming_schedules = Schedule.objects.filter(
        date__gte=now.date(),  # Today's date or later
        start_time__gte=now.time(),  # After now
        start_time__lte=two_hours_later.time(),  # Before 2 hours later
        status=True  # Only active lessons
    )

    print(f"Upcoming Schedules: {upcoming_schedules}")

    for schedule in upcoming_schedules:
        # Fetch all records (bookings) for this schedule
        records = Record.objects.filter(schedule=schedule, is_canceled=False)
        
        print(f"Records for Schedule {schedule.id}: {records}")

        for record in records:
            user = record.user

            if user.phone_number:
                try:
                    # Send a WhatsApp message
                    message_body = f"Напоминание: Ваш урок '{schedule.section.name}' начнется через 2 часа в {schedule.start_time}. Будьте готовы!"
                    client.messages.create(
                        body=message_body,
                        from_=TWILIO_WHATSAPP_FROM,
                        to=f'whatsapp:{user.phone_number}'
                    )
                    print(f"Уведомление отправлено пользователю {user.phone_number} на урок {schedule.section.name}")
                except Exception as e:
                    print(f"Ошибка при отправке сообщения на {user.phone_number}: {str(e)}")



@shared_task
def send_welcome_message(user_id):
    """Отправить уведомление пользователю, который успешно зарегистрировался"""
    user = CustomUser.objects.get(id=user_id)
    if user.phone_number:
        client.messages.create(
            body=f"Добро пожаловать, {user.first_name}! Вы успешно зарегистрировались.",
            from_=TWILIO_WHATSAPP_FROM,
            to=f'whatsapp:{user.phone_number}'
        )
        print(f"Приветственное сообщение отправлено на {user.phone_number}")


@shared_task
def notify_user_after_recording(record_id):
    """Уведомить пользователя, когда он успешно записан на урок."""
    record = Record.objects.get(id=record_id)
    user = record.user
    schedule = record.schedule

    if user.phone_number:
        try:
            # Отправить сообщение WhatsApp о записи на занятие
            message_body = f"Вы успешно записаны на урок '{schedule.section.name}', который пройдет {schedule.date} в {schedule.start_time}. Ждем вас!"
            client.messages.create(
                body=message_body,
                from_=TWILIO_WHATSAPP_FROM,
                to=f'whatsapp:{user.phone_number}'
            )
            print(f"Уведомление отправлено пользователю {user.phone_number} для записи на урок {schedule.section.name}")
        except Exception as e:
            print(f"Ошибка при отправке сообщения на {user.phone_number}: {str(e)}")
