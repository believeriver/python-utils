from django.contrib.auth import get_user_model
from rest_framework import serializers


# settings.py の AUTH_USER_MODEL　を参照して User を取得
# モデルを直接importするより柔軟
User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """ユーザ登録用シリアライザ"""

    # write_only=True: レスポンスJSONに含めない（セキュリティ）
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'},
    )

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'password']

    def create(self, validated_data):
        """
        UserManager.create_user() を呼び出してユーザを作成
        パスワードが自動でハッシュ化される
        """
        return User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password']
        )


class UserSerializer(serializers.ModelSerializer):
    """ログイン中ユーザー情報の取得"""

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'created_at']
        read_only_fields = ['id', 'created_at']  # これらのフィールドは更新不可

