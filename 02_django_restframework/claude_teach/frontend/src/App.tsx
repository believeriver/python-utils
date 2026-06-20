import { Routes, Route, Navigate } from "react-router-dom";
import PrivateRoute from "./components/common/PrivateRoute";
import PublicRoute from "./components/common/PublicRoute";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import MarketPage from "./pages/MarketPage";

const App = () => {
  return (
    <Routes>
      {/* 未認証ユーザのアクセス可能 */}
      <Route element={<PublicRoute />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Route>

      {/* 承認済みユーザのアクセス可能 */}
      <Route element={<PrivateRoute />}>
        <Route path="/market" element={<MarketPage />} />
      </Route>

      {/* ルートパスは /market にリダイレクト */}
      <Route path="/" element={<Navigate to="/market" replace />} />

      {/* 該当しないURLは /market にリダイレクト */}
      <Route path="*" element={<Navigate to="/market" replace />} />
    </Routes>
  )
}

export default App