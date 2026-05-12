from rest_framework import serializers
from .models import Company


class CompanySerializer(serializers.ModelSerializer):
    """
    Company モデルのシリアライザー
    ModelSerializer : モデルの定義を先に自動でフィールドを生成する
    """

    # ------------------------------------------------
    # カスタムフィールド
    # SerializerMethodField : メソッドの戻り値をフィールドにする
    # get_<フィールド名>　というメソッドを定義する約束
    # ------------------------------------------------
    stock_numeric = serializers.SerializerMethodField(
        help_text='株価を数値に変換したフィールド'
    )

    def get_stock_numeric(self, obj):
        """
        stock(例: "3,200")をfloatに変換して返す
        変換できない場合はNoneを返す
        :param obj:
        :return:
        """
        try:
            return float(obj.stock.replace(',', ''))
        except (ValueError, AttributeError):
            return None

    # ------------------------------------------------
    # Meta : シリアライザーの動作設定
    # ------------------------------------------------
    class Meta:
        model = Company # 対象のモデルを指定
        fields = [  # APIレスポンスに含めるフィールド
            'id',
            'code',
            'name',
            'stock',
            'stock_numeric',  # カスタムフィールドも忘れずに追加
            'dividend',
            'dividend_yield',
            'rank',
            'date',
            'created_at',
            'updated_at'
        ]
        # ------------------------------------------------
        # read_only_fields : APIリクエストで変更不可なフィールド
        # クライアントからの入力を受け付けない（自動生成等）
        # ------------------------------------------------
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
        ]

    # ------------------------------------------------
    # バリデーションメソッド
    # 1 フィールドレベルバリデーション
    # validate_<フィールド名> というメソッドを定義する約束
    # ------------------------------------------------
    def validate_code(self, value):
        """
        codeは4桁の数字でなければならない
        :param value:
        :return:
        """
        if not value.isdigit() or len(value) != 4:
            raise serializers.ValidationError('code must be a 4-digit number')
        return value

    # ------------------------------------------------
    # 2 オブジェクトレベルバリデーション
    # 複数フィールドまたいだ検証をする
    # validate というメソッドを定義する約束
    # ------------------------------------------------
    def validate(self, attrs):
        """
        rankが指定されている場合はdateも必須にする
        """
        if attrs.get('rank') and not attrs.get('date'):
            raise serializers.ValidationError(
                {'date': 'date is required when rank is specified'}
            )
        return attrs
