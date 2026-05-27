import { configureStore } from "@reduxjs/toolkit";
import marketReducer from "../features/market/marketSlice";


export const store = configureStore({
    reducer: {
        market: marketReducer, //機能ごとにリデューサーを追加
    },
})


// Typescript用の型定義
// useSelector / useDispatchで型安全にアクセスできるようにする
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;