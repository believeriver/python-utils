# apps/api/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import generics, serializers
from django.contrib.auth import get_user_model

User = get_user_model()


# パターン1: ログインユーザーのプロフィール取得
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user  # JWTから自動でユーザーを取得
        return Response({
            'id':         str(user.id),  # UUIDは文字列に変換
            'email':      user.email,
            'username':   user.username,
            'created_at': user.created_at,
        })


# パターン2: 管理者のみアクセス可能
class AdminOnlyView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        users = User.objects.all().values('id', 'email', 'username')
        return Response({'users': list(users)})


# パターン3: 認証あり・なしで返すデータを変える
class PublicOrPrivateView(APIView):

    def get(self, request):
        if request.user.is_authenticated:
            return Response({
                'message': f'Hello, {request.user.username}!',
                'secret':  'This is private data.',
            })
        return Response({
            'message': 'Hello, guest!',
        })
