import React, { useEffect, useState } from 'react';
import { useAppDispatch, useAppSelector } from '../app/hooks';
import type { RootState } from '../app/store';
import { fetchStockData, setStockCode } from '../features/stock/stockSlice';
import { fetchCompanyDetails } from '../features/company/companySlice';
import StockChart from './StockChart';
import CompanyList from './CompanyList';
import FinancialCharts from './FinancialCharts';
import './StockDashboard.css';

const StockDashboard: React.FC = () => {
  const dispatch = useAppDispatch();
  const { data, status, error, selectedCode } = useAppSelector((state: RootState) => state.stock);
  const { selectedCompany, detailsStatus } = useAppSelector((state: RootState) => state.company);
  const [inputCode, setInputCode] = useState(selectedCode);

  useEffect(() => {
    // Sync local input with selected code
    setInputCode(selectedCode);
  }, [selectedCode]);

  useEffect(() => {
    // Fetch both stock data and company details when selectedCode changes
    // We check status to avoid double fetching on initial load if handled elsewhere,
    // but here we want to react to selection changes.
    // Ideally we should check if data for this code is already present or just fetch.
    // For simplicity, we fetch when the component mounts or code changes.
    if (selectedCode) {
        if (status === 'idle' || data.length === 0 || selectedCode !== inputCode) {
            // Note: Simplification, realistically we'd check if currently loaded data matches selectedCode
             // But Redux state usually tracks "current" data.
        }
        dispatch(fetchStockData(selectedCode));
        dispatch(fetchCompanyDetails(selectedCode));
    }
  }, [dispatch, selectedCode]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputCode !== selectedCode) {
        dispatch(setStockCode(inputCode));
        // useEffect will handle the fetch
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

            {detailsStatus === 'loading' && <div className="loading">Loading financial data...</div>}
            {selectedCompany && selectedCompany.financials && selectedCompany.financials.length > 0 && (
                <section className="financials-section">
                    <FinancialCharts data={selectedCompany.financials} />
                </section>
            )}
        </main>
      </div>
    </div>
  );
};

export default StockDashboard;
