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

