import React, { useEffect, useState } from 'react';
import { useAppDispatch, useAppSelector } from '../app/hooks';
import { fetchStockData, setStockCode } from '../features/stock/stockSlice';
import StockChart from './StockChart';
import CompanyList from './CompanyList';
import './StockDashboard.css';

const StockDashboard: React.FC = () => {
  const dispatch = useAppDispatch();
  const { data, status, error, selectedCode } = useAppSelector((state) => state.stock);
  const [inputCode, setInputCode] = useState(selectedCode);

  useEffect(() => {
    // Sync local input with selected code
    setInputCode(selectedCode);
  }, [selectedCode]);

  useEffect(() => {
    if (status === 'idle') {
      dispatch(fetchStockData(selectedCode));
    }
  }, [status, dispatch, selectedCode]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputCode !== selectedCode) {
        dispatch(setStockCode(inputCode));
        dispatch(fetchStockData(inputCode));
    }
  };

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>Stock Market Visualizer</h1>
        <p className="subtitle">Real-time data for market insights</p>
      </header>

      <div className="dashboard-content">
        <aside className="sidebar">
            <CompanyList />
        </aside>

        <main className="main-content">
            <section className="controls">
                <form onSubmit={handleSearch} className="search-form">
                    <input 
                        type="text" 
                        value={inputCode} 
                        onChange={(e) => setInputCode(e.target.value)}
                        placeholder="Enter Stock Code"
                        className="stock-input"
                    />
                    <button type="submit" className="search-button">
                        Load Data
                    </button>
                </form>
            </section>

            <section className="chart-section">
                {status === 'loading' && <div className="loading">Loading market data...</div>}
                {status === 'failed' && <div className="error">Error: {error}</div>}
                {status === 'succeeded' && data.length > 0 && (
                    <div className="chart-card">
                        <div className="chart-header">
                            <h2>Performance: {selectedCode}</h2>
                            <span className="live-indicator">● Live</span>
                        </div>
                        <StockChart data={data} />
                    </div>
                )}
                {status === 'succeeded' && data.length === 0 && (
                    <div className="no-data">No data available for this code.</div>
                )}
            </section>
        </main>
      </div>
    </div>
  );
};

export default StockDashboard;
