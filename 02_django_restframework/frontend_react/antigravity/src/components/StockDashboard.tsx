import React, { useEffect, useState, useLayoutEffect } from 'react';
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
  const [selectedRange, setSelectedRange] = useState('1Y');

  useLayoutEffect(() => {
    // Sync local input with selected code
    setInputCode(selectedCode);
  }, [selectedCode]);

  useEffect(() => {
    // Function to calculate start date based on range
    const getStartDate = (range: string): string | undefined => {
        const now = new Date();
        switch (range) {
            case '1M':
                now.setMonth(now.getMonth() - 1);
                break;
            case '3M':
                now.setMonth(now.getMonth() - 3);
                break;
            case '1Y':
                now.setFullYear(now.getFullYear() - 1);
                break;
            case '5Y':
                now.setFullYear(now.getFullYear() - 5);
                break;
            case '10Y':
                now.setFullYear(now.getFullYear() - 10);
                break;
            case '20Y':
                now.setFullYear(now.getFullYear() - 20);
                break;
            case 'ALL':
            default:
                return undefined;
        }
        return now.toISOString().split('T')[0];
    };

    if (selectedCode) {
        const start = getStartDate(selectedRange);
        dispatch(fetchStockData({ code: selectedCode, start }));
        
        // Only fetch company details if code changed (not range)
        // Simplification: we might re-fetch details redundantly if we don't track prevCode
        // But details don't depend on range, so we can optimize if needed.
        // For now, let's just dispatch it. Ideally we should split this effect.
         dispatch(fetchCompanyDetails(selectedCode));
    }
  }, [dispatch, selectedCode, selectedRange]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputCode !== selectedCode) {
        dispatch(setStockCode(inputCode));
        // useEffect will handle the fetch
    }
  };

  const ranges = ['1M', '3M', '1Y', '5Y', '10Y', '20Y', 'ALL'];

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
                
                <div className="range-selector">
                    {ranges.map(range => (
                        <button
                            key={range}
                            className={`range-button ${selectedRange === range ? 'active' : ''}`}
                            onClick={() => setSelectedRange(range)}
                        >
                            {range}
                        </button>
                    ))}
                </div>

                {status === 'succeeded' && data.length > 0 && (
                    <div className="chart-card">
                        <div className="chart-header">
                            <div className="header-main">
                                <h2>{selectedCode}: {selectedCompany?.name || 'Loading...'}</h2>
                                <span className="live-indicator">● Live</span>
                            </div>
                            {selectedCompany?.information && (
                                <div className="company-info-bar">
                                    <div className="metrics">
                                        <span className="metric-badge">PER: {selectedCompany.information.per}x</span>
                                        <span className="metric-badge">PBR: {selectedCompany.information.pbr}x</span>
                                        <span className="metric-badge">Ind: {selectedCompany.information.industry}</span>
                                    </div>
                                    <p className="company-description">{selectedCompany.information.description}</p>
                                </div>
                            )}
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
