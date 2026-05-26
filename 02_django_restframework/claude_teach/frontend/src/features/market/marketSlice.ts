import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../../api/axiosConfig'; // API呼び出し用のモジュール

// Typescript:企業情報の型定義
export type Company = {
    id: number;
    code: string;
    name: string;
    stock: string;
    stock_numeric: number | null;
    dividend: string;
    dividend_yield: string;
    rank: number | null;
}

type MarketState = {
    companies: Company[];
    loading: boolean;
    error: string | null;
}

// 初期状態
const initialState: MarketState = {
    companies: [],
    loading: false,
    error: null,
}

// -----------------------------------------------
// createAsyncThunk : 非同期処理（API通信）を定義する
// 第一引数：アクション名（ユニークな文字列）
// 第二引数：非同期処理の関数（API呼び出しなど）
// -----------------------------------------------
export const fetchCompanies = createAsyncThunk(
    'market/fetchCompanies',
    async (_, { rejectWithValue }) => {
        try {
            const response = await api.get('/market/companies/');
            return response.data; // 成功時はデータを返す
        } catch (error) {
            console.error('Error fetching companies:', error);
            return rejectWithValue('企業情報の取得に失敗しました'); // 失敗時はエラーメッセージを返す
        }
    }
);

// -----------------------------------------------
// createSlice : スライス（機能ごとの状態管理）を定義する
// 第一引数：スライス名
// 第二引数：初期状態
// 第三引数：リデューサー（状態を更新する関数）
// -----------------------------------------------
const marketSlice = createSlice({
    name: 'market',
    initialState,
    reducers: {
        // ここに通常のアクションとリデューサーを定義できる
        // 例: setCompanies(state, action) { state.companies = action.payload; }
    },

    // 非同期処理の状態変化はここで処理する
    extraReducers: (builder) => {
        builder
            // API通信中
            .addCase(fetchCompanies.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            // API通信成功
            .addCase(fetchCompanies.fulfilled, (state, action) => {
                state.loading = false;
                state.companies = action.payload;
            })
            // API通信失敗
            .addCase(fetchCompanies.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload as string;
            });
    }
});

export default marketSlice.reducer;