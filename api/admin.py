from django.contrib import admin
from django.utils import timezone
from .models import Center, Section, Subscription, Enrollment, Feedback, SectionCategory, Schedule

class SectionInline(admin.TabularInline):
    model = Section
    extra = 1

class ScheduleInline(admin.TabularInline):
    model = Schedule
    extra = 1

@admin.register(Center)
class CenterAdmin(admin.ModelAdmin):
    list_display = ('name', 'location')
    search_fields = ('name', 'location')
    filter_horizontal = ('sections',)  # Используем виджет для работы с ManyToManyField

@admin.register(SectionCategory)
class SectionCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_centers', 'category')
    search_fields = ('name', 'category__name')
    list_filter = ('category',)

    def get_centers(self, obj):
        return ", ".join([center.name for center in obj.centers.all()])
    
    get_centers.short_description = 'Centers'


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('center', 'section', 'day_of_week', 'start_time', 'end_time')
    search_fields = ('center__name', 'section__name', 'day_of_week')
    list_filter = ('day_of_week', 'center', 'section')

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_iin', 'center', 'section', 'type', 'name')
    search_fields = ('user__email', 'user__iin', 'center__name', 'section__name', 'type', 'name')

    def user_iin(self, obj):
        return obj.user.iin
    user_iin.short_description = 'IIN'

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'section', 'time', 'confirmed', 'confirmation_time')
    search_fields = ('user__email', 'section__name')
    list_filter = ('confirmed', 'time')

    actions = ['cancel_enrollment', 'set_time_to_now', 'set_time_to_today']

    def cancel_enrollment(self, request, queryset):
        queryset.update(confirmed=False, confirmation_time=None)
        self.message_user(request, "Selected enrollments have been canceled.")
    cancel_enrollment.short_description = "Cancel selected enrollments"

    def set_time_to_now(self, request, queryset):
        now = timezone.now()
        queryset.update(time=now)
        self.message_user(request, "Time set to now for selected enrollments.")
    set_time_to_now.short_description = "Set time to now"

    def set_time_to_today(self, request, queryset):
        today = timezone.now().date()
        queryset.update(time=today)
        self.message_user(request, "Time set to today for selected enrollments.")
    set_time_to_today.short_description = "Set time to today"

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'center', 'feedback')
    search_fields = ('user__email', 'center__name', 'feedback')
