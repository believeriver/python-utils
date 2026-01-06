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

export interface FinancialData {
    fiscal_year: string;
    sales: string | number;
    operating_margin: number;
    eps: number | null;
    equity_ratio: number;
    operating_cash_flow: number;
    cash_and_equivalents: number;
    dividend_per_share: number | null;
    payout_ratio: number | null;
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

export interface CompanyDetails extends Company {
    financials: FinancialData[];
}

interface CompanyState {
    companies: Company[];
    selectedCompany: CompanyDetails | null;
    status: 'idle' | 'loading' | 'succeeded' | 'failed';
    detailsStatus: 'idle' | 'loading' | 'succeeded' | 'failed';
    error: string | null;
}

const initialState: CompanyState = {
    companies: [],
    selectedCompany: null,
    status: 'idle',
    detailsStatus: 'idle',
    error: null,
};

export const fetchCompanies = createAsyncThunk(
    'company/fetchCompanies',
    async () => {
        const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
        const response = await axios.get<Company[]>(`${baseUrl}/api_irbank/companies/`);
        return response.data;
    }
);

export const fetchCompanyDetails = createAsyncThunk(
    'company/fetchCompanyDetails',
    async (code: string) => {
        const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
        const response = await axios.get<CompanyDetails>(`${baseUrl}/api_irbank/companies/${code}/`);
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
            })
            .addCase(fetchCompanyDetails.pending, (state) => {
                state.detailsStatus = 'loading';
            })
            .addCase(fetchCompanyDetails.fulfilled, (state, action) => {
                state.detailsStatus = 'succeeded';
                state.selectedCompany = action.payload;
            })
            .addCase(fetchCompanyDetails.rejected, (state, action) => {
                state.detailsStatus = 'failed';
                state.error = action.error.message || 'Failed to fetch company details';
            });
    },
});

export default companySlice.reducer;
