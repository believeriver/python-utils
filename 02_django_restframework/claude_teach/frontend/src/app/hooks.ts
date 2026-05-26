// TypeScriptで useSelector / useDispatch を型安全に使用するためのフック
import { useDispatch, useSelector } from "react-redux";
import type { RootState, AppDispatch } from "./store";

// 型付きの useDispatch / useSelector をエクスポート
// これを使うことで毎回型を書かなくて良くなる
export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector = <T>(selector: (state: RootState) => T) => {
    return useSelector(selector);
};