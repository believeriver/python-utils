from django.urls import path

from . import views

urlpatterns = [
    path('tweets/', views.TweetListView.as_view(), name='tweets-list'),
    path('user/register/', views.UserRegisterView.as_view(), name='user-register'),
]