from rest_framework import viewsets, permissions
from .models import Company
from .serializers import CompanySerializer


# class CompanyViewSet(viewsets.ModelViewSet):
class CompanyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    viewsets.ModelViewSet
    企業情報のCRUD APIを提供するViewSet

    ModelVIewSetが自動生成するエンドポイント：
    GET /api/companies/            : list()     企業一覧の取得
    POST /api/companies/           : create()   企業の新規作成
    GET /api/companies/<code>/     : retrieve() 企業の詳細取得
    PUT /api/companies/<code>/     : update()   企業の全更新
    PATCH /api/companies/<code>/   : partial_update() 企業の部分更新
    DELETE /api/companies/<code>/  : destroy() 企業の削除
    """
    """
    viewsets.ReadOnlyModelViewSet
    読み取り専用ViewSet
    GET のみ許可、POST / PUT / PATCH / DELETE は 405 Method Not Allowed
    """

    # 返すデータの元となるクエリセット
    queryset = Company.objects.all()

    # シリアライザークラスの指定
    serializer_class = CompanySerializer

    # URLのルックアップキー（デフォルトはpk=id)
    # codeフィールドで /companies/<code>/ にアクセスできるようにする
    lookup_field = 'code'

    # パーミッション：誰でも閲覧可能（認証不要）
    # settings.pyのDEFAULT_PERMISSION_CLASSESを上書きして、IsAuthenticatedをAllowAnyに変更
    permission_classes = [permissions.AllowAny]

