from django.db import models


class Company(models.Model):
    """
    企業マスターテーブル
    スクレイピングで取得した企業情報を格納する
    """

    # ------------------------------------------------
    # フィールド定義
    # ------------------------------------------------

    # 認証コード（例：7203）
    # unique=True : 同じコードを２件登録できない
    # db_index=True : コードで検索する際のパフォーマンス向上
    code = models.CharField(
        max_length=10,
        unique=True,
        db_index=True,
        verbose_name='証券コード'
    )

    # 企業名（例：トヨタ自動車）
    name = models.CharField(
        max_length=120,
        verbose_name='企業名'
    )

    # 株価（スクレイピング結果をそのまま格納するため、CharFieldで定義）
    # blank=True : 空欄を許可する（スクレイピングで取得できない場合があるため）
    # null=True : データベース上でNULLを許可する（blank=Trueとセットで使用）
    stock = models.CharField(
        max_length=32,
        blank=True,
        null=True,
        verbose_name='株価'
    )

    # 配当（スクレイピング結果をそのまま格納するため、CharFieldで定義）
    # blank=True : 空欄を許可する（スクレイピングで取得できない場合があるため）
    # null=True : データベース上でNULLを許可する（blank=True)
    dividend = models.CharField(
        max_length=32,
        blank=True,
        null=True,
        verbose_name='配当金'
    )

    # 配当利回り
    dividend_yield = models.CharField(
        max_length=16,
        blank=True,
        null=True,
        verbose_name='配当利回り'
    )

    # 高配当ランキング
    rank = models.IntegerField(
        null = True,
        blank = True,
        verbose_name='高配当ランキング'
    )

    # データ取得日
    date = models.DateField(
        null = True,
        blank = True,
        verbose_name='データ取得日'
    )

    # レコード作成び（登録時に自動セット）
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='作成日時'
    )

    # レコード更新日時（更新のたびに自動セット）
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='更新日時'
    )

    # ------------------------------------------------
    # メタ情報: テーブルの動作設定
    # ------------------------------------------------
    class Meta:
        # デフォルトの並び順（rank昇順、nullは最後）
        ordering = ['rank']

        # 管理画面での表示名（単数形）
        verbose_name        = '企業'
        verbose_name_plural = '企業一覧'

        # 複合インデックス（codeとdateの組み合わせで一意制約を設定）
        indexes = [
            models.Index(fields=['code', 'date'])
        ]

    # ------------------------------------------------
    # 文字列表現 __str__（管理画面やシェルでの表示用）
    # ------------------------------------------------
    def __str__(self):
        return f'{self.code} : {self.name}'

    # ------------------------------------------------
    # クラスメソッド：「あれば更新、なければ作成」
    # スクレイピング結果の保存に使う
    # ------------------------------------------------
    @classmethod
    def get_or_create_and_update(cls, _code, _name, _stock,
                                 _dividend, _dividend_yield,
                                 _rank, _date):
        """
        証券コードで検索し、存在すれば更新、なければ新規作成する
        :param _code:
        :param _name:
        :param _stock:
        :param _dividend:
        :param _dividend_yield:
        :param _rank:
        :param _date:
        :return: (instance, created)
          created: Trueなら新規作成、Falseなら更新
        """
        obj, created = cls.objects.get_or_create(
            code=_code, # codeで検索して、なければ新規作成
            defaults={  #新規作成時だけ使われる値
                'name': _name,
                'stock': _stock,
                'dividend': _dividend,
                'dividend_yield': _dividend_yield,
                'rank': _rank,
                'date': _date
            }
        )

        if not created:
            # 既存レコードが見つかった場合は、値を更新して保存する
            obj.name = _name
            obj.stock = _stock
            obj.dividend = _dividend
            obj.dividend_yield = _dividend_yield
            obj.rank = _rank
            obj.date = _date
            obj.save()

        return obj, created
