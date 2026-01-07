import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

interface User {
    id: number;
    email: string;
    username: string; // Add other fields as necessary from myprofile
}

interface AuthState {
    user: User | null;
    token: string | null;
    status: 'idle' | 'loading' | 'succeeded' | 'failed';
    error: string | null;
}

const initialState: AuthState = {
    user: null,
    token: localStorage.getItem('access_token'), // Persist token
    status: 'idle',
    error: null,
};

// Async thunk to login user
export const loginUser = createAsyncThunk(
    'auth/loginUser',
    async ({ email, password }: { email: string; password: string }) => {
        const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
        const response = await axios.post(`${baseUrl}/authen/jwt/create`, {
            email,
            password,
        });
        return response.data; // Expected { access: "token", refresh: "token" } usually, or just access
    }
);

// Async thunk to register user
export const registerUser = createAsyncThunk(
    'auth/registerUser',
    async ({ email, password }: { email: string; password: string }) => {
        const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
        const response = await axios.post(`${baseUrl}/api_auth/register/`, {
            email,
            password,
        });
        return response.data;
    }
);

// Async thunk to fetch my profile
export const fetchProfile = createAsyncThunk(
    'auth/fetchProfile',
    async (_, { getState }) => {
        const state = getState() as any; // Need to import RootState to use correctly, but avoided cyclic dependency for now
        const token = state.auth.token;
        
        if (!token) throw new Error('No token found');

        const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
        const response = await axios.get(`${baseUrl}/api_auth/myprofile/`, {
            headers: {
                Authorization: `JWT ${token}`,
            },
        });
        return response.data;
    }
);

const authSlice = createSlice({
    name: 'auth',
    initialState,
    reducers: {
        logout(state) {
            state.user = null;
            state.token = null;
            state.status = 'idle';
            state.error = null;
            localStorage.removeItem('access_token');
        },
    },
    extraReducers: (builder) => {
        builder
            // Login
            .addCase(loginUser.pending, (state) => {
                state.status = 'loading';
                state.error = null;
            })
            .addCase(loginUser.fulfilled, (state, action) => {
                state.status = 'succeeded';
                state.token = action.payload.access; // Assuming response has 'access' property
                localStorage.setItem('access_token', action.payload.access);
            })
            .addCase(loginUser.rejected, (state, action) => {
                state.status = 'failed';
                state.error = action.error.message || 'Login failed';
            })
            // Register
            .addCase(registerUser.pending, (state) => {
                state.status = 'loading';
                state.error = null;
            })
            .addCase(registerUser.fulfilled, (state) => {
                state.status = 'succeeded';
                // Automatically logging in after register might need explicit action or user flow.
                // For now just success state.
            })
            .addCase(registerUser.rejected, (state, action) => {
                state.status = 'failed';
                state.error = action.error.message || 'Registration failed';
            })
            // Profile
            .addCase(fetchProfile.fulfilled, (state, action) => {
                state.user = action.payload; // Adjust based on actual profile response text/json
            });
    },
});

export const { logout } = authSlice.actions;
export default authSlice.reducer;
