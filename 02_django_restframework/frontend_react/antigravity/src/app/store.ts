import { configureStore } from '@reduxjs/toolkit';
import stockReducer from '../features/stock/stockSlice';
import companyReducer from '../features/company/companySlice';
import authReducer from '../features/auth/authSlice';

export const store = configureStore({
  reducer: {
    stock: stockReducer,
    company: companyReducer,
    auth: authReducer,
  },
});

// Infer the `RootState` and `AppDispatch` types from the store itself
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
