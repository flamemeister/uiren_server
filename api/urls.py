from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CenterViewSet, SectionViewSet, SubscriptionViewSet, EnrollmentViewSet, FeedbackViewSet, SectionCategoryViewSet, confirm_attendance, redirect_to_whatsapp


router = DefaultRouter()
router.register(r'centers', CenterViewSet)
router.register(r'sections', SectionViewSet)
router.register(r'subscriptions', SubscriptionViewSet)
router.register(r'enrollments', EnrollmentViewSet)
router.register(r'feedbacks', FeedbackViewSet)
router.register(r'section-categories', SectionCategoryViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('confirm_attendance/', confirm_attendance, name='confirm_attendance'),
    path('contact_manager/', redirect_to_whatsapp, name='contact_manager'),
]
