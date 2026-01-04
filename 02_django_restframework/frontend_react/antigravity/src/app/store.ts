import { configureStore } from '@reduxjs/toolkit';
import stockReducer from '../features/stock/stockSlice';

export const store = configureStore({
  reducer: {
    stock: stockReducer,
  },
});

// Infer the `RootState` and `AppDispatch` types from the store itself
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
