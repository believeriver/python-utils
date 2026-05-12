from rest_framework.routers import DefaultRouter
from .views import CompanyViewSet

# Router: ViewSet からURLパターンを自動生成する仕組み
router = DefaultRouter()

# ViewSetをルーターに登録
# 第一引数：URLのプレフィックス（例: 'companies' → /companies/）
# 第二引数：ViewSetクラス
# basename: URL名のprefix, reverse()で使う（例: 'company' → company-list, company-detail）
router.register(r'companies', CompanyViewSet, basename='company')

urlpatterns = router.urls
