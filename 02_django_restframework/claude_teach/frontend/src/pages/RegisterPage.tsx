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
        <div style={styles.container}>
            <div style={styles.card}>
                <h1 style={styles.title}>新規登録</h1>

                {error && (
                    <p style={styles.error}>
                        登録に失敗しました。入力内容を確認してください。
                    </p>
                )}

                <form onSubmit={handleSubmit}>
                    <div style={styles.field}>
                        <label>メールアドレス</label>
                        <input 
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            style={styles.input}
                            required
                        />
                    </div>

                    <div style={styles.field}>
                        <label>ユーザー名</label>
                        <input 
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            style={styles.input}
                            required
                        />
                    </div>

                    <div style={styles.field}>
                        <label>パスワード（８文字以上）</label>
                        <input 
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            style={styles.input}
                            required
                            minLength={8}
                        />
                    </div>

                    <button 
                        type="submit"
                        disabled={loading}
                        style={styles.button}
                    >
                        {loading ? '登録中...' : '登録する'}
                    </button>
                </form>

                <p style={{marginTop: '1rem', textAlign: 'center'}}>
                    すでにアカウントをお持ちの方は
                    <span onClick={onLogin} style={styles.link}>
                        ログイン
                    </span>
                </p>
            </div>
        </div>
    )

}

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
        textAlign: 'center',
        marginBottom: '1.5rem',
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
        backgroundColor: '#27ae60',
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

export default RegisterPage
