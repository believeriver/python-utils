import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../../api/axiosConfig'; // API呼び出し用のモジュール

// Typescript:ユーザー情報の型定義
type User = {
    id: number;
    email: string;
    username: string;
}

type AuthState = {
    user: User | null;
    isAuthenticated: boolean;
    loading: boolean;
    error: string | null;
}

// localStorageからトークンを取得して初期状態を設定
const initialState: AuthState = {
    user: null,
    isAuthenticated: !!localStorage.getItem('access_token'), // トークンがあれば認証済みとする
    loading: false,
    error: null,
}


// -----------------------------------------------
// ユーザー登録
// -----------------------------------------------
export const registerUser = createAsyncThunk(
    'auth/register',
    async (
        data: { email: string; username: string; password: string },
        { rejectWithValue }
    ) => {
        try {
            const response = await api.post('/auth/register/', data);
            return response.data; // 成功時はユーザーデータを返す
        } catch (error: any) {
            console.error('Error registering user:', error);
            return rejectWithValue(
                error.response?.data || 'ユーザー登録に失敗しました'
            ); // 失敗時はエラーメッセージを返す
        }
    }
)