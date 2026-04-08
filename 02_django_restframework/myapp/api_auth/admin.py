# apps/api_auth/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model

User = get_user_model()


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    # 一覧画面に表示するカラム
    list_display = ['email', 'username', 'is_active', 'is_staff', 'created_at']

    # 右サイドバーのフィルター
    list_filter = ['is_active', 'is_staff', 'is_superuser']

    # 検索対象フィールド
    search_fields = ['email', 'username']

    # デフォルトのソート順
    ordering = ['-created_at']

    # ユーザー詳細・編集画面のレイアウト
    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        ('基本情報', {
            'fields': ('username',)
        }),
        ('権限', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('日時', {
            'fields': ('created_at',)
        }),
    )

    # ユーザー新規作成画面のレイアウト
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )

    # 編集不可フィールド
    readonly_fields = ['created_at']