from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CenterViewSet, SectionViewSet, SubscriptionViewSet, EnrollmentViewSet, FeedbackViewSet, SectionCategoryViewSet, confirm_attendance, initiate_payment, handle_kaspi_response


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
    path('initiate_payment/', initiate_payment, name='initiate_payment'),
    path('handle_kaspi_response/', handle_kaspi_response, name='handle_kaspi_response'),

]
