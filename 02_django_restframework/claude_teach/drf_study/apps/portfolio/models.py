import uuid
from django.db import models
from django.conf import settings


class Portfolio(models.Model):
    """
    ポートフォリオ明細テーブル
    ログインユーザの保有銘柄を管理する
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # ログインユーザと紐付け
    # settings.AUTH_USER_MODELは、Djangoのユーザモデルを参照するための設定値
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='portfolios',
        verbose_name='ユーザー')

    # 証券コード（Companyお出るとは外部キーではなくコードで紐付け）
    # 理由：スクレイピングデータが存在しない銘柄も登録できるようになる
    company_code = models.CharField(
        max_length=10,
        verbose_name='証券コード'
    )

    company_name = models.CharField(
        max_length=128,
        verbose_name='企業名'
    )

    # 保有株数
    shares = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='保有株数'
    )

    # 取得単価
    purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='取得単価'
    )

    # 取得日
    purchased_at = models.DateField(
        verbose_name='取得日'
    )

    memo = models.TextField(
        blank=True,
        verbose_name='メモ'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('company_code',)
        verbose_name = 'ポートフォリオ'
        verbose_name_plural = 'ポートフォリオ一覧'

        # 同じユーザが同じ銘柄を同じ日に二重登録できない
        unique_together = [['user', 'company_code', 'purchased_at']]

    def __str__(self):
        return f'{self.user} : {self.company_code} {self.company_name}'


