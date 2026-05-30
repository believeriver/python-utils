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
        <div style={styles.container}>
            <div >
                <h1>ログイン</h1>
            </div>
        </div>
      )
}

// インラインスタイル
const styles: { [key: string]: React.CSSProperties } = {
    container: {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        backgroundColor: '#f5f5f5',
    },
}

export default LoginPage;