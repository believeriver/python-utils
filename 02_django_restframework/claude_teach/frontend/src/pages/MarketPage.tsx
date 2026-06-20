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
                
            </div>

        </div>
    )
}

export default MarketPage