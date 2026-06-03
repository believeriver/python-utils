import { useState, useEffect } from "react";
import { useAppDispatch, useAppSelector } from "../app/hooks";
import { loginUser, clearError } from "../features/auth/authSlice";

type Props = {
    onSuccess: () => void   //ログイン成功時のコールバック
    onRegister: () => void  //登録画面への切り替え
}

const LoginPage = ({ onSuccess, onRegister }: Props) => {
    const dispatch = useAppDispatch()
    const { loading, error, isAuthenticated } = 
      useAppSelector((state) => state.auth)

      const [email, setEmail] = useState<string>('')
      const [password, setPassword] = useState<string>('')

      // ログイン成功時に親コンポーネントに通知
      useEffect(() => {
        if (isAuthenticated){
            onSuccess()
        }
      }, [isAuthenticated, onSuccess])

      // 画面を離れる時にエラーをクリア
      useEffect(() => {
        return () => {
            dispatch(clearError())
        }
      }, [dispatch])

      const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault() // フォームのデフォルト送信を防ぐ
        dispatch(loginUser({ email, password}))
      }

      return (
        <div className="min-h-screen bg-gray-100 flex items-center justify-center">
            <div className="bg-white rounded-lg shadow-md p-8 w-full max-w-md">

                <h1 className="text-2x1 font-bold text-center text-gray-800 md-6">
                    ログイン
                </h1>

                {error && (
                    <div className="bg-red-50 text-red-600 px-5 py-3 rounded mb-4 text-sm">
                        メールアドレスまたはパスワードが正しくありません
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            メールアドレス
                        </label>
                        <input 
                            type="emal"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            パスワード
                        </label>
                        <input 
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full py-2 px4 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-medium rounded-md transition-colors"
                    >
                        {loading ? 'ログイン中...' : 'ログイン'}
                    </button>
                </form>

                <p className="mt-4 text-center text-sm text-gray-600">
                    アカウントをお持ちでない方は
                    <span
                        onClick={onRegister}
                        className="text-blue-600 hover:underline cursor-pointer ml-1"
                    >
                        新規登録
                    </span>
                </p>
            </div>
        </div>
      )
}

export default LoginPage;