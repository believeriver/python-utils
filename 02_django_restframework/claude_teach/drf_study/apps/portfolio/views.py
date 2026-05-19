from rest_framework import viewsets, permissions
from .models import Portfolio
from .serializers import PortfolioSerializer


class PortfolioViewSet(viewsets.ModelViewSet):
    """
    ポートフォリオのCRUDを提供するViewSet

    重要：ログインユーザのデータだけを返す
    他のユーザのデータは一切見えない
     - GET /api/portfolio/items/         : ポートフォリオの一覧を取得
     - POST /api/portfolio/items/        : 新しいポートフォリオを作成
     - GET /api/portfolio/items/{id}/    : 特定のポートフォリオを取得
     - PUT /api/portfolio/items/{id}/    : 特定のポートフォリオを更新
     - DELETE /api/portfolio/items/{id}/ : 特定のポートフォリオを削除
    """
    serializer_class = PortfolioSerializer
    permission_classes = [permissions.IsAuthenticated] # 認証されたユーザのみアクセス可能

    def get_queryset(self):
        """
        クエリセットをログインユーザに絞り込む
        これがないと全ユーザのデータが帰ってしまう

        request.user -> JWTトークンから取得したユーザ
        :return:
        """
        return Portfolio.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """
        新規作成時にユーザを自動セットする
        クライアントからuserを送らなくても自動セットされる
        """
        serializer.save(user=self.request.user)
