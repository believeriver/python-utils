import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import api from "../../api/axiosConfig"; // API呼び出し用のモジュール

// Typescript:ユーザー情報の型定義
type User = {
  id: number;
  email: string;
  username: string;
};

type AuthState = {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
};

// localStorageからトークンを取得して初期状態を設定
const initialState: AuthState = {
  user: null,
  isAuthenticated: !!localStorage.getItem("access_token"), // トークンがあれば認証済みとする
  loading: false,
  error: null,
};

// -----------------------------------------------
// ユーザー登録
// -----------------------------------------------
export const registerUser = createAsyncThunk(
  "auth/register",
  async (
    data: { email: string; username: string; password: string },
    { rejectWithValue },
  ) => {
    try {
      const response = await api.post("/auth/register/", data);
      return response.data; // 成功時はユーザーデータを返す
    } catch (error: any) {
      console.error("Error registering user:", error);
      return rejectWithValue(
        error.response?.data || "ユーザー登録に失敗しました",
      ); // 失敗時はエラーメッセージを返す
    }
  },
);

// -----------------------------------------------
// ユーザーログイン
// -----------------------------------------------
export const loginUser = createAsyncThunk(
  "auth/login",
  async (data: { email: string; password: string }, { rejectWithValue }) => {
    try {
      const response = await api.post("/auth/login/", data);
      const { access, refresh } = response.data;
      // トークンをlocalStorageに保存
      localStorage.setItem("access_token", access);
      localStorage.setItem("refresh_token", refresh);
      return response.data; // 成功時はユーザーデータを返す
    } catch (error: any) {
      console.error("Error logging in:", error);
      return rejectWithValue(error.response?.data || "ログインに失敗しました"); // 失敗時はエラーメッセージを返す
    }
  },
);

// -----------------------------------------------
// ログイン中ユーザ情報取得
// -----------------------------------------------
export const fetchMe = createAsyncThunk(
  "auth/fetchMe",
  async (_NEVER, { rejectWithValue }) => {
    try {
      const response = await api.get("/auth/me/");
      return response.data; // 成功時はユーザーデータを返す
    } catch (error: any) {
      console.error("Error fetching user info:", error);
      return rejectWithValue(
        error.response?.data || "ユーザー情報の取得に失敗しました",
      ); // 失敗時はエラーメッセージを返す
    }
  },
);

// -----------------------------------------------
// authSlice : 認証関連の状態管理を定義するスライス
// -----------------------------------------------
const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    // ログアウトアクション
    logout: (state) => {
      state.user = null;
      state.isAuthenticated = false;
      state.error = null;
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
    },
    // エラーのクリア
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // ユーザー登録
      .addCase(registerUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(registerUser.fulfilled, (state) => {
        state.loading = false;
      })
      .addCase(registerUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      // ログイン
      .addCase(loginUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(loginUser.fulfilled, (state) => {
        state.loading = false;
        state.isAuthenticated = true;
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      // ログイン中ユーザ情報取得
      .addCase(fetchMe.fulfilled, (state, action) => {
        state.user = action.payload;
      });
  },
});

export const { logout, clearError } = authSlice.actions;
export default authSlice.reducer;
