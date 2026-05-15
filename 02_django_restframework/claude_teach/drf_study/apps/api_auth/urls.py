from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegisterView, MeView, LogoutView

urlpatterns = [
    # ユーザ登録
    path('register/', RegisterView.as_view(), name='register'),

    # ログイン（JWTトークンの発行）
    # TokenObtainPairView : simplejwtが提供する既成View
    # email + password を受け取り access / refresh トークンを返す
    path('login/', TokenObtainPairView.as_view(), name='login'),

    # アクセストークンの更新
    # TokenRefreshView : simplejwtが提供する既成View
    # refresh トークンを受け取り新しい access トークンを返す
    path('refresh/', TokenRefreshView.as_view(), name='refresh'),

    # ログアウト（トークンの無効化）
    path('logout/', LogoutView.as_view(), name='logout'),

    # ログイン中ユーザの情報取得
    path('me/', MeView.as_view(), name='me'),
]