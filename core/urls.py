from django.contrib import admin
from django.urls import path, include
from api.views import index


urlpatterns = [
    path('admin/', admin.site.urls),
    path('user/', include('user.urls')),  # Adjust based on your actual app names
    path('api/', include('api.urls')),
    path('', index, name='index'),

]
