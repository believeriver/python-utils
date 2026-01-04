import { createSlice, createAsyncThunk, type PayloadAction } from '@reduxjs/toolkit';
import axios from 'axios';

// Interface for the Stock Data based on User's JSON response
export interface StockDataPoint {
  year: string;
  value: number;
}

interface StockState {
  data: StockDataPoint[];
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
  selectedCode: string;
}

const initialState: StockState = {
  data: [],
  status: 'idle',
  error: null,
  selectedCode: '9986', // Default to the example code provided
};

// Async thunk to fetch stock data
export const fetchStockData = createAsyncThunk(
  'stock/fetchStockData',
  async (code: string) => {
    // Ideally this URL base should be in an env variable or config
    // Note: User provided http://127.0.0.1:8000/api_irbank/stock/9986/
    // We will dynamically insert the code.
    const response = await axios.get<StockDataPoint[]>(`http://127.0.0.1:8000/api_irbank/stock/${code}/`);
    return response.data;
  }
);

const stockSlice = createSlice({
  name: 'stock',
  initialState,
  reducers: {
    setStockCode(state, action: PayloadAction<string>) {
      state.selectedCode = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchStockData.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchStockData.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.data = action.payload;
      })
      .addCase(fetchStockData.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message || 'Failed to fetch stock data';
      });
  },
});

export const { setStockCode } = stockSlice.actions;
export default stockSlice.reducer;
