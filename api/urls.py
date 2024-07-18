from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CenterViewSet, SectionViewSet, SubscriptionViewSet, EnrollmentViewSet, FeedbackViewSet
router = DefaultRouter()
router.register(r'centers', CenterViewSet)
router.register(r'sections', SectionViewSet)
router.register(r'subscriptions', SubscriptionViewSet)
router.register(r'enrollments', EnrollmentViewSet)
router.register(r'feedbacks', FeedbackViewSet)

urlpatterns = [
    path('', include(router.urls)),

]
