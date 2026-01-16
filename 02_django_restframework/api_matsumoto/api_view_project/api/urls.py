from django.urls import path
from . import views

app_name = 'api'


urlpatterns = [
    path('item/', views.ItemView.as_view(), name='item'),
]