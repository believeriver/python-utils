from django.urls import path
from . import views

app_name = 'apiv2'


urlpatterns = [
    path('item/', views.ItemModelView.as_view(), name='item-model'),
    path('item/<int:pk>/', views.ItemModelDetailView.as_view(), name='item-model-detail'),
]