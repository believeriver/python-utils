import { useState, useEffect } from 'react' 
import { useAppSelector, useAppDispatch } from './app/hooks'
import { fetchCompanies } from './features/market/marketSlice'
import { fetchMe, logout } from './features/auth/authSlice'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'

type Page = 'login' | 'register' | 'market'

const App = () => {
  const dispatch = useAppDispatch()
  const { isAuthenticated, user } = useAppSelector((state) => state.auth)
  const { companies, loading, error } = useAppSelector((state) => state.market)

  // 現在表示するページ
  const [currentPage, setCurrentPage] = useState<Page>(
    isAuthenticated ? 'market' : 'login'
  )

  // 認証ずみの場合はユーザー情報と企業データを取得
  useEffect(() => {
    if(isAuthenticated){
      dispatch(fetchMe())
      dispatch(fetchCompanies())
      setCurrentPage('market')
    }
  }, [isAuthenticated, dispatch])

  const handleLogout = () => {
    dispatch(logout())
    setCurrentPage('login')
  }

  //ページ振り分け
  if (currentPage == 'login'){
    return (
      <LoginPage 
        onSuccess={() => setCurrentPage('market')}
        onRegister={() => setCurrentPage('register')}
      />
    )
  }

  if (currentPage === 'register') {
    return (
      <RegisterPage 
        onSuccess={() => setCurrentPage('login')}
        onLogin={() => setCurrentPage('login')}
      />
    )
  }

  // 企業一覧画面
  return (
    <div style={{ padding: '2rem'}}>

      {/* ヘッダー */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '2rem',
      }}>
        <h1>企業一覧</h1>
        <div>
          {user && <span style={ {marginRight: '2rem'}}>{user.username} さん</span>}
          <button
            onClick={handleLogout}
            style={{
              padding: '8px 16px',
              backgroundColor: '#e74c3c',
              color: '#fff',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
          >
            ログアウト
          </button>
        </div>
      </div>

      {loading && <p>読み込み中...</p>}
      {error && <p style={{ color: 'red'}}>{error}</p>}

      <table style={{ borderCollapse: 'collapse', width: '100%'}}>
        <thead>
          <tr style={{ backgroundColor: '#ddd'}}>
            <th style={{padding: '8px', border: '1px solid #ccc'}}>証券コード</th>
            <th style={{padding: '8px', border: '1px solid #ccc'}}>企業名</th>
            <th style={{padding: '8px', border: '1px solid #ccc'}}>株価</th>
            <th style={{padding: '8px', border: '1px solid #ccc'}}>配当利回り</th>
            <th style={{padding: '8px', border: '1px solid #ccc'}}>ランキング</th>
          </tr>
        </thead>
        <tbody>
          {companies.map((company) => (
            <tr key={company.code}>
              <td style={{padding: '8px', border: '1px solid #ccc'}}>{company.code}</td>
              <td style={{padding: '8px', border: '1px solid #ccc'}}>{company.name}</td>
              <td style={{padding: '8px', border: '1px solid #ccc'}}>{company.stock}</td>
              <td style={{padding: '8px', border: '1px solid #ccc'}}>{company.dividend_yield}</td>
              <td style={{padding: '8px', border: '1px solid #ccc'}}>{company.rank}</td>
            </tr>
          ))}
        </tbody>
      </table>

    </div>
  )
}

export default App