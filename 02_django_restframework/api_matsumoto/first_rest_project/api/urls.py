from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('json-example/', views.json_example, name='json_example'),
    path('country-datetime/', views.country_datetime, name='country_datetime'),
]