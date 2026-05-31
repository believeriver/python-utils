import { useEffect } from 'react';
import { useAppDispatch, useAppSelector } from './app/hooks';
import { fetchCompanies } from './features/market/marketSlice';


const App = () => {
  const dispatch = useAppDispatch();

  // Reduxから状態を取得
  const companies = useAppSelector((state) => state.market.companies);
  const loading = useAppSelector((state) => state.market.loading);
  const error = useAppSelector((state) => state.market.error);

  // コンポーネントが表示されたときに企業情報を取得する
  useEffect(() => {
    dispatch(fetchCompanies());
  }, [dispatch]);


  // ローディング中やエラー発生時の表示
  if (loading) return <div>Loading...</div>;
  // エラーがあれば表示
  if (error) return <p style={{color: 'red'}}>{error}</p>;

  return (
    <div style={{ padding: '2rem' }}>
      <h1>企業一覧</h1>
      <table style={{ borderCollapse: 'collapse', width: '100%'}}>
        <thead>
          <tr style={{ backgroundColor: '#ddd'}}>
            <th style={{ border: '1px solid #ddd', padding: '8px' }}>証券コード</th>
            <th style={{ border: '1px solid #ddd', padding: '8px' }}>企業名</th>
            <th style={{ border: '1px solid #ddd', padding: '8px' }}>株価</th>
            <th style={{ border: '1px solid #ddd', padding: '8px' }}>配当利回り</th>
            <th style={{ border: '1px solid #ddd', padding: '8px' }}>ランキング</th>
          </tr>
        </thead>
        <tbody>
          {companies.map((company) => (
            <tr key={company.id}>
              <td style={{ border: '1px solid #ddd', padding: '8px' }}>{company.code}</td>
              <td style={{ border: '1px solid #ddd', padding: '8px' }}>{company.name}</td>
              <td style={{ border: '1px solid #ddd', padding: '8px' }}>{company.stock}</td>
              <td style={{ border: '1px solid #ddd', padding: '8px' }}>{company.dividend_yield}</td>
              <td style={{ border: '1px solid #ddd', padding: '8px' }}>{company.rank}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default App;