/**
 * @file EquityChart.tsx
 * Компонент графика накопленной доходности (Equity Curve).
 */

import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';
import { EquityCurvePoint } from '../types/api';

interface EquityChartProps {
  data: EquityCurvePoint[];
}

/**
 * Отрисовывает область (Area Chart) с накопленным результатом по дням.
 */
export const EquityChart: React.FC<EquityChartProps> = ({ data }) => {
  // Преобразуем строковые значения PnL в числа для графика
  const chartData = data.map(point => ({
    ...point,
    cumPnlNum: parseFloat(point.cum_pnl),
    dayPnlNum: parseFloat(point.day_pnl),
  }));

  return (
    <div className="card" style={{ height: '400px' }}>
      <h3 style={{ marginTop: 0, fontSize: '1rem' }}>Cumulative PnL (Equity Curve)</h3>
      <ResponsiveContainer width="100%" height="90%">
        <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="colorPnl" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10b981" stopOpacity={0.1}/>
              <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
          <XAxis 
            dataKey="date" 
            fontSize={12}
            tickMargin={10}
            axisLine={false}
            tickLine={false}
          />
          <YAxis 
            fontSize={12}
            axisLine={false}
            tickLine={false}
            tickFormatter={(value) => `${value}`}
          />
          <Tooltip 
            formatter={(value: number) => [`${value.toFixed(2)} USDT`, 'Cumulative PnL']}
            labelStyle={{ fontWeight: 'bold' }}
          />
          <Area 
            type="monotone" 
            dataKey="cumPnlNum" 
            stroke="#10b981" 
            fillOpacity={1} 
            fill="url(#colorPnl)" 
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};
