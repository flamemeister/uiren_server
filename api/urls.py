from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CenterViewSet, SectionViewSet, SubscriptionViewSet, ScheduleViewSet, RecordViewSet, SectionCategoryViewSet, FeedbackViewSet

router = DefaultRouter()
router.register(r'centers', CenterViewSet)
router.register(r'sections', SectionViewSet)
router.register(r'categories', SectionCategoryViewSet)
router.register(r'subscriptions', SubscriptionViewSet)
router.register(r'schedules', ScheduleViewSet)
router.register(r'records', RecordViewSet)
router.register(r'feedbacks', FeedbackViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('attendance/', RecordViewSet.as_view({'post': 'confirm_attendance'})),
]
