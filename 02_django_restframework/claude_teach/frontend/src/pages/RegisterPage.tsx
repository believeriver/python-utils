import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../app/hooks";
import { registerUser, clearError } from "../features/auth/authSlice";


const RegisterPage = () => {
    const navigate = useNavigate()
    const dispatch = useAppDispatch()
    const { loading, error } = 
      useAppSelector((state) => state.auth)
    
    const [email, setEmail] = useState<string>('')
    const [username, setUsername] = useState<string>('')
    const [password, setPassword] = useState<string>('')

    useEffect(() => {
        return () => {
            dispatch(clearError())}
    }, [dispatch])

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault() // フォームのデフォルト送信を防ぐ
        const result = await dispatch(registerUser({ email, username, password }))

        // 登録成功時に親コンポーネントに通知
        if (registerUser.fulfilled.match(result)) {
            navigate('/login')
        }
    }

    return (
        <div className="min-h-screen bg-gray-100 flex items-center justify-center">
            <div className="bg-white rounded-lg shadow-md p-8 w-full max-w-md">
                <h1 className="text-2x1 font-bold text-center text-gray-800 mb-6">
                    新規登録
                </h1>

                {error && (
                    <div className="bg-red-50 text-red-600 px-4 py-3 rounded mb-4 text-sm">
                        {/* 登録に失敗しました。入力内容を確認してください。 */}
                        {typeof error === 'string'
                          ? error
                          : typeof error === 'object'
                            ? Object.entries(error).map(([field, messages]) => (
                                <p key={field}>
                                    {Array.isArray(messages) ? messages.join(' ') : String(messages)}
                                </p>
                            ))
                            : '登録に失敗しました'
                        }
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            メールアドレス
                        </label>
                        <input 
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                            required
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            ユーザー名
                        </label>
                        <input 
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                            required
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            パスワード（８文字以上）
                        </label>
                        <input 
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                            required
                            minLength={8}
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full py-2 px-4 bg-green-600 hover:bg-green-700 disabled:bg-green-300 text-white font-medium rounded-md transition-colors"
                    >
                        {loading ? '登録中...' : '登録する'}
                    </button>
                </form>

                <p className="mt-4 text-center text-sm text-gray-600">
                    すでにアカウントお持ちの方は
                    {/* <span
                        onClick={onLogin}
                        className="text-blue-600 hover:underline cursor-pointer ml-1"
                    >
                        ログイン
                    </span> */}
                    <Link to="/login" className="text-blue-600 hover:underline ml-1">
                        ログイン
                    </Link>
                </p>
            </div>      
        </div>
    )
}

export default RegisterPage
