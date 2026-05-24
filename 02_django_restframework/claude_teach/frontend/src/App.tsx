import {useState, useEffect} from 'react';
import api from './api/axiosConfig';

// TypesScript:APIレスポンスの型定義
type Company = {
  id: number
  code: string
  name: string
  stock: string
  stock_numeric: number | null
  dividned: string
  dividend_yield: string
  rank: number | null
}


const App = () => {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // useEffect: コンポーネントが表示された時に実行される
  // 第２引数の[]は、「初回レンダリング時のみ実行」の意味
  useEffect(() => {
    const fetchCompanies = async () => {
      try {
        const response = await api.get('/market/companies/');
        setCompanies(response.data);
      } catch (err) {
        setError('データの取得に失敗しました');
        console.error(err);
      } finally {
        // 成功・失敗どちらでもローディング終了
        setLoading(false);
      }
    };

    fetchCompanies();
  }, []);

  // ローディング中やエラー発生時の表示
  if (loading) return <div>Loading...</div>;

  // エラーがあれば表示
  if (error) return <p style={{color: 'red'}}>{error}</p>;

  return (
    <div style={{ padding: '2rem' }}>
      <h1>企業情報</h1>
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