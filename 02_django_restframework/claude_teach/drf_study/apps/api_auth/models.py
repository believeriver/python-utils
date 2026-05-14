import uuid
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin, UserManager)


class UserManager(BaseUserManager):
    """
    カスタムUserモデル用のマネージャー
    create_user / create_superuser メソッドを定義
    """

    def create_user(self, email, password=None, **extra_fields):
        """
        通常ユーザの作成
        extra_fields: is_staff, is_superuser などの追加フィールド
        """
        if not email:
            raise ValueError('Users must have an email address')

        # メールアドレスを正規化（ドメイン部分を小文字に）
        email = self.normalize_email(email)

        user = self.model(email=email, **extra_fields)

        # パスワードをハッシュ化して保存(平文保存禁止）
        user.set_password(password)  # パスワードをハッシュ化して保存
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        管理者ユーザの作成
        manage.py createsuperuser コマンドで呼び出される
        is_staff=True, is_superuser=True を強制
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


    class User(AbstractBaseUser, PermissionsMixin):
        """
        カスタムUserモデル

        AbstractBaseUser: パスワード管理、認証関連(password / last_login)の基本機能を提供
        PermissionsMixin: 権限管理（is_superuser, groups, user_permissions）を提供
        """

        # -----------------------------------------------------------
        # 主キー：UUID（外部公開しても推測されない）
        # -----------------------------------------------------------
        id = models.UUIDField(
            primary_key=True,
            default=uuid.uuid4,
            editable=False,       #管理画面で編集不可
        )

        # -----------------------------------------------------------
        # ログインキー：メールアドレス（ユニーク）
        # -----------------------------------------------------------
        email = models.EmailField(
            unique=True,
            verbose_name='email address',
        )

        # -----------------------------------------------------------
        # プロフィール
        # -----------------------------------------------------------
        username = models.CharField(
            max_length=64,
            verbose_name='username',
        )

        # -----------------------------------------------------------
        # 権限フラグ
        # -----------------------------------------------------------
        is_active = models.BooleanField(
            default=True,
            verbose_name='active',
        )
        is_staff = models.BooleanField(
            default=False,
            verbose_name='staff status',
        )

        # -----------------------------------------------------------
        # タイムスタンプ
        # -----------------------------------------------------------
        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)

        # -----------------------------------------------------------
        # マネージャーの指定
        # -----------------------------------------------------------
        objects = UserManager()

        # ログインに使うフィールドを username -> email に変更
        USERNAME_FIELD = 'email'

        # createusuperuser コマンドで追加入力を求めるフィールド
        REQUIRED_FIELDS = ['username']

        class Meta:
            verbose_name = 'user'
            verbose_name_plural = 'users'

        def __str__(self):
            return self.email



