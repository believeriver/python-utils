from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer, UserSerializer

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """
    ユーザ登録用APIビュー
    POST /api/auth/register/ でユーザ登録を処理
     - リクエストボディに email, username, password を含むJSONを送る
     - 成功すると201 Createdとユーザ情報を返す
     - 失敗すると400 Bad Requestとエラーメッセージを返す
     generics.CreateAPIView: POSTのみを提供する汎用View
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]  # 認証不要（誰でもアクセス


class MeView(generics.RetrieveAPIView):
    """
    ログイン中ユーザの情報を取得するAPIビュー
    GET /api/auth/me/ で現在のユーザ情報を返す
     - 認証が必要（JWTトークンをヘッダーに含める）
     - 成功すると200 OKとユーザ情報を返す
     - 失敗すると401 Unauthorizedを返す
    generics.RetrieveAPIView: GETのみを提供する汎用View
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # URLパラメータではなくトークンからユーザを消す
        return self.request.user


class LogoutView(APIView):
    """
    ログアウト用APIビュー
    POST /api/auth/logout/ でユーザをログアウト（トークンを無効化）
     - 認証が必要（JWTトークンをヘッダーに含める）
     - 成功すると204 No Contentを返す
     - 失敗すると400 Bad Requestを返す
     リフレッシュトークンをブラックリストに追加して無効化する
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            # クライアントからリフレッシュトークンを受け取る
            refresh_token = request.data['refresh']
            token = RefreshToken(refresh_token)
            print('DEBUG refresh_token:', refresh_token)
            token.blacklist()  # トークンをブラックリストに追加して無効化
            return Response(
                {'message': 'Logged out successfully.'},
                status=status.HTTP_200_OK)
        except Exception as e:
            print(f'DEBUG logout error: {e}')
            return Response(
                {'error': 'Invalid token or logout failed.'},
                status=status.HTTP_400_BAD_REQUEST)

