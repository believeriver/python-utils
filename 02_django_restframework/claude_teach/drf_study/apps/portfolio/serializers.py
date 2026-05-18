from rest_framework import serializers
from .models import Portfolio


class PortfolioSerializer(serializers.ModelSerializer):
    """
    ポートフォリオのシリアライザ
    """

    # 取得金額（株数 × 株価）を計算して返すフィールド
    total_cost = serializers.SerializerMethodField()

    def get_total_cost(self, obj):
        return float(obj.shares * obj.purchase_price)

    class Meta:
        model = Portfolio
        fields = [
            'id',
            'company_code',
            'company_name',
            'shares',
            'purchase_price',
            'total_cost',  # 計算フィールドを追加
            'purchased_at',
            'memo',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_company_code(self, value):
        """証券コードは４桁の英数字"""
        if not value.isalnum() or len(value) != 4:
            raise serializers.ValidationError("証券コードは４桁の英数字でなければなりません。")
        return value.upper()