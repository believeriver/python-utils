import React, { useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '../app/hooks';
import { fetchCompanies, type Company } from '../features/company/companySlice';
import { setStockCode, fetchStockData } from '../features/stock/stockSlice';
import './CompanyList.css';

const CompanyList: React.FC = () => {
    const dispatch = useAppDispatch();
    const { companies, status, error } = useAppSelector((state) => state.company);
    const { selectedCode } = useAppSelector((state) => state.stock);

    useEffect(() => {
        if (status === 'idle') {
            dispatch(fetchCompanies());
        }
    }, [status, dispatch]);

    const handleSelectCompany = (code: string) => {
        dispatch(setStockCode(code));
        dispatch(fetchStockData(code));
    };

    if (status === 'loading') {
        return <div className="company-list-loading">Loading Companies...</div>;
    }

    if (status === 'failed') {
        return <div className="company-list-error">Error: {error}</div>;
    }

    return (
        <div className="company-list-container">
            <h3>Registered Companies</h3>
            <div className="company-list">
                {companies.map((company: Company) => {
                    const isSelected = company.code === selectedCode;
                    return (
                        <div 
                            key={company.code} 
                            className={`company-card ${isSelected ? 'selected' : ''}`}
                            onClick={() => handleSelectCompany(company.code)}
                        >
                            <div className="company-info-header">
                                <span className="company-code">{company.code}</span>
                                <span className="company-price">¥{company.stock}</span>
                            </div>
                            <div className="company-name">{company.name}</div>
                            <div className="company-details">
                                <div className="detail-item">
                                    <span className="label">Dividend</span>
                                    <span className="value">{company.dividend}%</span>
                                </div>
                                <div className="detail-item">
                                    <span className="label">Rank</span>
                                    <span className="value">#{company.dividend_rank}</span>
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default CompanyList;
