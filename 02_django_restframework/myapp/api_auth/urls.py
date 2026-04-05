# apps/api_auth/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RegisterView, CustomTokenObtainPairView, LogoutView

urlpatterns = [
    path('register/', RegisterView.as_view(),              name='auth-register'),
    path('login/',    CustomTokenObtainPairView.as_view(), name='auth-login'),
    path('refresh/',  TokenRefreshView.as_view(),          name='auth-refresh'),
    path('logout/',   LogoutView.as_view(),                name='auth-logout'),
]
