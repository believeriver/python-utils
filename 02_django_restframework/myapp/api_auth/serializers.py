# apps/api_auth/serializers.py
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model  = User
        fields = ['id', 'email', 'username', 'password', 'password2']
        read_only_fields = ['id']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password': 'Passwords do not match'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        return User.objects.create_user(**validated_data)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['email']    = self.user.email
        data['username'] = self.user.username
        return data


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        self.token = attrs['refresh']
        return attrs

    def save(self, **kwargs):
        try:
            RefreshToken(self.token).blacklist()
        except TokenError:
            raise serializers.ValidationError({'refresh': 'Token is invalid or expired'})

class ChangePasswordSerializer(serializers.Serializer):
    """
    2026.4.8 パスワード変更用シリアライザを追加
     - current_password: 現在のパスワード（検証用）
     - new_password: 新しいパスワード（8文字以上）
     - new_password2: 新しいパスワードの確認（new_passwordと一致する必要あり）
     - validate_current_password: 現在のパスワードが正しいか検証
     - validate: new_passwordとnew_password2が一致するか検証
     - save: パスワードを更新してユーザーを保存
     - これにより、ユーザーは現在のパスワードを入力して新しいパスワードに変更できるようになります。
     POST /api/auth/change-password/
    """
    current_password = serializers.CharField(write_only=True)
    new_password     = serializers.CharField(write_only=True, min_length=8)
    new_password2    = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect')
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({'new_password': 'Passwords do not match'})
        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """
    2026.4.9 プロフィール更新用シリアライザを追加
    """
    class Meta:
        model  = User
        fields = ['email', 'username']

    def validate_email(self, value):
        user = self.context['request'].user
        # 自分以外が同じemailを使っていないか確認
        if User.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError('This email is already in use')
        return value

    def update(self, instance, validated_data):
        instance.email    = validated_data.get('email',    instance.email)
        instance.username = validated_data.get('username', instance.username)
        instance.save()
        return instance

