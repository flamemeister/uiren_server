from django.contrib import admin
from .models import Center, Section, Subscription, Enrollment, Feedback

@admin.register(Center)
class CenterAdmin(admin.ModelAdmin):
    list_display = ('name', 'location')

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'center')

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'center', 'type', 'name')

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'section', 'time')

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'center', 'feedback')
