import { Navigate, Outlet } from 'react-router-dom'
import { useAppSelector } from '../../app/hooks'


/*
認証済みユーザーのみアクセス可能とするルート
未認証の場合は /login にリダイレクトする
*/

const PrivateRoute = () => {
    const { isAuthenticated } = useAppSelector((state) => state.auth)

    // 未認証の場合、ログイン画面へリダイレクト
    if (!isAuthenticated){
        return <Navigate to="/login" replace />
    }

    // 認証済みの場合、子ルートを表示
    // Outlet : ネストされたルート（子コンポーネント）の表示位置
    return <Outlet />
}

export default PrivateRoute