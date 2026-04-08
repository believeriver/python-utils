# apps/api_auth/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from .serializers import (
    RegisterSerializer,
    CustomTokenObtainPairSerializer,
    LogoutSerializer,
    ChangePasswordSerializer,
    ProfileUpdateSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    queryset           = User.objects.all()
    serializer_class   = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_205_RESET_CONTENT)


class ChangePasswordView(APIView):
    """パスワード変更API"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}  # ← serializerにrequestを渡す
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'message': 'Password changed successfully'},
            status=status.HTTP_200_OK
        )


class ProfileUpdateView(APIView):
    """プロフィール更新API"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """現在のユーザー情報を取得"""
        user = request.user
        return Response({
            'id':         str(user.id),
            'email':      user.email,
            'username':   user.username,
            'created_at': user.created_at,
        })

    def patch(self, request):
        """ユーザー情報を部分更新"""
        serializer = ProfileUpdateSerializer(
            instance=request.user,
            data=request.data,
            partial=True,                   # ← PATCH挙動を明示
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
