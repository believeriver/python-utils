import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../app/hooks";
import { fetchCompanies } from "../features/market/marketSlice";
import { fetchMe, logout } from "../features/auth/authSlice";


const MarketPage = () => {
    const navigate = useNavigate()
    const dispatch = useAppDispatch()
    const { user } = useAppSelector((state) => state.auth)
    const { companies, loading, error } = useAppSelector((state) => state.market)

    useEffect(() => {
        dispatch(fetchMe())
        dispatch(fetchCompanies())
    }, [dispatch])

    const handleLogout = () => {
        dispatch(logout())
        navigate('/login')
    }

    return (
        <div className="min-h-screen bg-gray-50 p-8">
            {/* ヘッダー */}
            <div className="flex justify-between items-center mb-8">
                <h1 className="text-2x1 font-bold text-gray-800">企業一覧</h1>
                <div className="flex items-center gap-4">
                    {user && (
                        <span className="text-gray-600">{user.username} さん</span>
                    )}
                    <button
                        onClick={handleLogout}
                        className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-md text-sm transition-colors"
                    >
                        ログアウト
                    </button>
                </div>
            </div>

            {loading && <p className="text-gray-500">読み込み中...</p>}
            {error   && <p className="text-red-500">{error}</p>}

            {/* テーブル */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
                <table className="w-full">
                    <thead className="bg-gray-100">
                        <tr>
                            <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">証券コード</th>
                            <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">企業名</th>
                            <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">株価</th>
                            <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">配当利回り</th>
                            <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">ランキング</th>
                        </tr>
                    </thead>
                </table>
                <tbody className="divide-y divide-gray-100">
                    {companies.map((company) => (
                        <tr key={company.code} className="hover:bg-gray-50">
                            <td className="px-4 py-3 text-sm">{company.code}</td>
                            <td className="px-4 py-3 text-sm">{company.name}</td>
                            <td className="px-4 py-3 text-sm">{company.stock}</td>
                            <td className="px-4 py-3 text-sm">{company.dividend_yield}</td>
                            <td className="px-4 py-3 text-sm">{company.rank}</td>
                        </tr>
                    ))}
                </tbody>
            </div>
        </div>
    )
}

export default MarketPage