import React from 'react';
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart
} from 'recharts';
import type { StockDataPoint } from '../features/stock/stockSlice';

interface StockChartProps {
  data: StockDataPoint[];
}

const StockChart: React.FC<StockChartProps> = ({ data }) => {
  // Creating a reversed copy of the data to show chronological order (Oldest -> Newest)
  // And formatting date for display
  const chartData = [...data].reverse().map(item => ({
    ...item,
    formattedDate: new Date(item.year).toLocaleDateString(),
    timestamp: new Date(item.year).getTime(),
  }));

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="custom-tooltip" style={{
            backgroundColor: 'rgba(20, 20, 30, 0.9)',
            border: '1px solid #334',
            padding: '10px',
            borderRadius: '8px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
            color: '#fff'
        }}>
          <p className="label" style={{ margin: 0, fontWeight: 'bold', color: '#a0a0b0' }}>{label}</p>
          <p className="intro" style={{ margin: '5px 0 0', color: '#00d0ff', fontSize: '1.2em' }}>
             ¥{payload[0].value.toLocaleString()}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div style={{ width: '100%', height: 400, marginTop: '20px' }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={chartData}
          margin={{
            top: 20,
            right: 30,
            left: 20,
            bottom: 5,
          }}
        >
          <defs>
            <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#00d0ff" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#00d0ff" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
          <XAxis 
            dataKey="formattedDate" 
            stroke="#666" 
            tick={{ fill: '#888', fontSize: 12 }}
            minTickGap={30}
          />
          <YAxis 
            stroke="#666"
            tick={{ fill: '#888', fontSize: 12 }}
            domain={['auto', 'auto']}
            tickFormatter={(value) => `¥${value}`}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area 
            type="monotone" 
            dataKey="value" 
            stroke="#00d0ff" 
            strokeWidth={2}
            fillOpacity={1} 
            fill="url(#colorValue)" 
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

export default StockChart;
