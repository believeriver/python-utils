import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

export interface CompanyInformation {
    industry: string;
    description: string;
    per: number;
    psr: number;
    pbr: number;
    updated_at: string;
}

export interface Company {
    code: string;
    name: string;
    stock: string;
    dividend: number;
    dividend_rank: number;
    dividend_update: string;
    information: CompanyInformation | null;
}

interface CompanyState {
    companies: Company[];
    status: 'idle' | 'loading' | 'succeeded' | 'failed';
    error: string | null;
}

const initialState: CompanyState = {
    companies: [],
    status: 'idle',
    error: null,
};

export const fetchCompanies = createAsyncThunk(
    'company/fetchCompanies',
    async () => {
        const response = await axios.get<Company[]>('http://127.0.0.1:8000/api_irbank/companies/');
        return response.data;
    }
);

const companySlice = createSlice({
    name: 'company',
    initialState,
    reducers: {},
    extraReducers: (builder) => {
        builder
            .addCase(fetchCompanies.pending, (state) => {
                state.status = 'loading';
            })
            .addCase(fetchCompanies.fulfilled, (state, action) => {
                state.status = 'succeeded';
                state.companies = action.payload;
            })
            .addCase(fetchCompanies.rejected, (state, action) => {
                state.status = 'failed';
                state.error = action.error.message || 'Failed to fetch companies';
            });
    },
});

export default companySlice.reducer;
