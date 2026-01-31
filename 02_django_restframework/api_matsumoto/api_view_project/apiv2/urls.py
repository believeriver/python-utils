from django.urls import path
from . import views

app_name = 'apiv2'


urlpatterns = [
    path('item/', views.ItemModelView.as_view(), name='item-model'),
    path('item/<int:pk>/', views.ItemModelDetailView.as_view(), name='item-model-detail'),
    path('user/', views.UserModelView.as_view(), name='user-model'),
    path('user/<int:pk>/', views.UserModelDetailView.as_view(), name='user-model-detail'),
    path('product/', views.ProductModelView.as_view(), name='product-model'),
    path('product/<int:pk>/', views.ProductModelDetailView.as_view(), name='product-model-detail'),
]