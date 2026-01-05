import React from 'react';
import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  AreaChart,
  Area
} from 'recharts';
import type { FinancialData } from '../features/company/companySlice';
import './FinancialCharts.css';

interface FinancialChartsProps {
  data: FinancialData[];
}

const FinancialCharts: React.FC<FinancialChartsProps> = ({ data }) => {
  // Sort data by fiscal year just in case
  const chartData = [...data].sort((a, b) => 
    parseInt(a.fiscal_year) - parseInt(b.fiscal_year)
  );

  const formatCurrency = (value: number | string) => {
    const num = Number(value);
    if (Math.abs(num) >= 100000000) {
      return `¥${(num / 100000000).toFixed(0)}億`;
    }
    return `¥${num.toLocaleString()}`;
  };

  return (
    <div className="financial-charts-container">
      <h3 className="section-title">Financial Trends</h3>
      
      <div className="charts-grid">
        {/* Sales and Operating Margin */}
        <div className="chart-item">
            <h4>Sales & Operating Margin</h4>
            <ResponsiveContainer width="100%" height={250}>
                <ComposedChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                    <XAxis dataKey="fiscal_year" stroke="#666" tick={{fill: '#888', fontSize: 11}} />
                    <YAxis yAxisId="left" stroke="#666" tickFormatter={formatCurrency} width={60} tick={{fill: '#888', fontSize: 11}} />
                    <YAxis yAxisId="right" orientation="right" stroke="#666" tickFormatter={(v) => `${v}%`} tick={{fill: '#888', fontSize: 11}} />
                    <Tooltip 
                        contentStyle={{ backgroundColor: '#14141e', border: '1px solid #334', borderRadius: '8px' }}
                        itemStyle={{ color: '#fff' }}
                        formatter={(value: any, name: string | undefined) => {
                            if (name === 'Sales') return [formatCurrency(value as number), name];
                            if (name === 'Operating Margin') return [`${value}%`, name];
                            return [value, name];
                        }}
                    />
                    <Legend />
                    <Bar yAxisId="left" dataKey="sales" name="Sales" fill="#007aff" barSize={20} radius={[4, 4, 0, 0]} />
                    <Line yAxisId="right" type="monotone" dataKey="operating_margin" name="Operating Margin" stroke="#00d0ff" strokeWidth={2} dot={{r: 3}} />
                </ComposedChart>
            </ResponsiveContainer>
        </div>

        {/* Cash Flow */}
        <div className="chart-item">
            <h4>Cash Flow</h4>
            <ResponsiveContainer width="100%" height={250}>
                <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                    <XAxis dataKey="fiscal_year" stroke="#666" tick={{fill: '#888', fontSize: 11}} />
                    <YAxis stroke="#666" tickFormatter={formatCurrency} width={60} tick={{fill: '#888', fontSize: 11}} />
                    <Tooltip 
                        contentStyle={{ backgroundColor: '#14141e', border: '1px solid #334', borderRadius: '8px' }}
                        formatter={(value: any) => formatCurrency(value)}
                    />
                    <Legend />
                    <Bar dataKey="operating_cash_flow" name="Operating CF" fill="#00ff88" barSize={20} radius={[4, 4, 0, 0]} />
                    <Bar dataKey="cash_and_equivalents" name="Cash & Eq." fill="#ffae00" barSize={20} radius={[4, 4, 0, 0]} />
                </BarChart>
            </ResponsiveContainer>
        </div>

        {/* EPS & Dividend */}
        <div className="chart-item">
            <h4>EPS & Dividend</h4>
            <ResponsiveContainer width="100%" height={250}>
                <ComposedChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                    <XAxis dataKey="fiscal_year" stroke="#666" tick={{fill: '#888', fontSize: 11}} />
                    <YAxis stroke="#666" tick={{fill: '#888', fontSize: 11}} />
                    <Tooltip 
                         contentStyle={{ backgroundColor: '#14141e', border: '1px solid #334', borderRadius: '8px' }}
                    />
                    <Legend />
                    <Bar dataKey="eps" name="EPS" fill="#a461ff" barSize={20} radius={[4, 4, 0, 0]} />
                    <Bar dataKey="dividend_per_share" name="Dividend" fill="#ff4d4d" barSize={20} radius={[4, 4, 0, 0]} />
                </ComposedChart>
            </ResponsiveContainer>
        </div>

        {/* Equity Ratio */}
        <div className="chart-item">
            <h4>Equity Ratio (%)</h4>
            <ResponsiveContainer width="100%" height={250}>
                <AreaChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                    <XAxis dataKey="fiscal_year" stroke="#666" tick={{fill: '#888', fontSize: 11}} />
                    <YAxis stroke="#666" tickFormatter={(v) => `${v}%`} tick={{fill: '#888', fontSize: 11}} domain={[0, 100]} />
                    <Tooltip 
                         contentStyle={{ backgroundColor: '#14141e', border: '1px solid #334', borderRadius: '8px' }}
                         formatter={(value: any) => `${value}%`}
                    />
                    <Area type="monotone" dataKey="equity_ratio" name="Equity Ratio" stroke="#00d0ff" fill="rgba(0, 208, 255, 0.2)" />
                </AreaChart>
            </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default FinancialCharts;
