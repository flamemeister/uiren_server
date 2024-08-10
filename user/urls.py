from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, UserByTokenView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import UserProfileView


router = DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    path('register/', UserViewSet.as_view({'post': 'create'}), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('user/', UserByTokenView.as_view(), name='user_by_token'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),

    path('', include(router.urls)),
]
