import { useState, useEffect } from "react";
import { useAppDispatch, useAppSelector } from "../app/hooks";
import { registerUser, clearError } from "../features/auth/authSlice";

type Props = {
    onSuccess: () => void   //登録成功時のコールバック
    onLogin: () => void    //ログイン画面への切り替え
}

const RegisterPage = ({ onSuccess, onLogin }: Props) => {
    const dispatch = useAppDispatch()
    const { loading, error } = 
      useAppSelector((state) => state.auth)
    
    const [email, setEmail] = useState<string>('')
    const [username, setUsername] = useState<string>('')
    const [password, setPassword] = useState<string>('')

    useEffect(() => {
        return () => {
            dispatch(clearError())
        }
    }, [dispatch])

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault() // フォームのデフォルト送信を防ぐ
        const result = await dispatch(registerUser({ email, username, password }))

        // 登録成功時に親コンポーネントに通知
        if (registerUser.fulfilled.match(result)) {
            onSuccess() 
        }
    }

    return (
        <div className="min-h-screen bg-gray-100 flex items-center justify-center">
            <div className="bg-white rounded-lg shadow-md p-8 w-full max-w-md">
                <h1 className="text-2x1 font-bold text-center text-gray-800 mb-6">
                    新規登録
                </h1>

            </div>
            
        </div>
    )

}

export default RegisterPage
