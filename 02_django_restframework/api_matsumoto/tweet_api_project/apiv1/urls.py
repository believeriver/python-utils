from django.urls import path
from rest_framework.authtoken import views as token_views

from . import views

urlpatterns = [
    path('tweets/', views.TweetListView.as_view(), name='tweets-list'),
    path('user/register/', views.UserRegisterView.as_view(), name='user-register'),
    path('api-token-auth/', token_views.obtain_auth_token, name='api-token-auth'),
    path('tweets/<int:pk>/', views.TweetUpdateDetailView.as_view(), name='tweet-update-delete'),
    # path('user/login/', views.UserLoginView.as_view(), name='user-login'),
    path('login_cookie/', views.login_cookie, name='login-cookie'),
]