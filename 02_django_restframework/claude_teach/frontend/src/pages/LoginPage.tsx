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
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
    },
    card: {
        backgroundColor: '#fff',
        padding: '2rem',
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        width: '100%',
        maxWidth: '400px',
    },
    title: {
        marginBottom: '1.5rem',
        textAlign: 'center',
    },
    field: {
        marginBottom: '1rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '4px',
    },
    input: {
        padding: '8px',
        border: '1px solid #ccc',
        borderRadius: '4px',
        fontSize: '1rem',
    },
    button: {
        width: '100%',
        padding: '10px',
        backgroundColor: '#4a90e2',
        color: '#fff',
        border: 'none',
        borderRadius: '4px',
        fontSize: '1rem',
        cursor: 'pointer',
        marginTop: '0.5rem',
    },
    error: {
        color: '#e74c3c',
        backgroundColor: '#fdecea',
        padding: '8px',
        borderRadius: '4px',
        marginBottom: '1rem',
    },
    link: {
        color: '#4a90e2',
        cursor: 'pointer',
        marginLeft: '4px',
    },
}

export default LoginPage;