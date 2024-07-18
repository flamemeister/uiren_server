from django.contrib import admin
from .models import Center, Section, Subscription, Enrollment, Feedback

@admin.register(Center)
class CenterAdmin(admin.ModelAdmin):
    list_display = ('name', 'location')
    search_fields = ('name', 'location')

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'center')
    search_fields = ('name', 'center__name')

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'center', 'type', 'name')
    search_fields = ('user__email', 'center__name', 'type', 'name')

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'section', 'time', 'confirmed', 'confirmation_time')
    search_fields = ('user__email', 'section__name')
    list_filter = ('confirmed', 'time')

    actions = ['cancel_enrollment']

    def cancel_enrollment(self, request, queryset):
        queryset.update(confirmed=False, confirmation_time=None)
        self.message_user(request, "Selected enrollments have been canceled.")
    cancel_enrollment.short_description = "Cancel selected enrollments"

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'center', 'feedback')
    search_fields = ('user__email', 'center__name', 'feedback')
