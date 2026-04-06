# apps/api/urls.py
from django.urls import path
from .views import ProfileView, AdminOnlyView, PublicOrPrivateView

urlpatterns = [
    path('profile/',         ProfileView.as_view(),        name='profile'),
    path('admin-only/',      AdminOnlyView.as_view(),       name='admin-only'),
    path('public-or-private/', PublicOrPrivateView.as_view(), name='public-or-private'),
]
