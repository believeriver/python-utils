import { Navigate, Outlet } from "react-router-dom";
import { useAppSelector } from "../../app/hooks";

/*
未認証ユーザのみアクセス可能にするルート
認証済みの場合は /market にリダイレクトする
（ログイン済みなのにログイン画面を表示しないようにする）
*/
const PublicRoute = () => {
    const { isAuthenticated } = useAppSelector((state) => state.auth)

    if (isAuthenticated) {
        return <Navigate to="/market" replace />
    }

    return <Outlet />
}

export default PublicRoute