from django.urls import path

from . import views

urlpatterns = [
    path('tweets/', views.TweetListView.as_view(), name='tweet-list'),
]