/**
 * @file Metrics.tsx
 * Компонент для отображения ключевых метрик эффективности торговли.
 */

import React from 'react';
import { StatsResponse } from '../types/api';
import { formatMoney, parseMoney } from '../utils/formatMoney';

interface MetricsProps {
  stats: StatsResponse | null;
}

/**
 * Отображает строку карточек с основными показателями (PnL, Win Rate и др.).
 * Расцвечивает значения в зависимости от их прибыльности/убыточности.
 */
export const Metrics: React.FC<MetricsProps> = ({ stats }) => {
  if (!stats) return <div className="metrics-grid">Загрузка метрик...</div>;

  const netPnlNum = parseMoney(stats.net_pnl);
  const pnlClass = netPnlNum > 0 ? 'text-success' : netPnlNum < 0 ? 'text-danger' : '';

  return (
    <div className="metrics-grid">
      <div className="metric-card">
        <div className="metric-label">Net PnL</div>
        <div className={`metric-value ${pnlClass}`}>
          {formatMoney(stats.net_pnl)} USDT
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-label">Win Rate</div>
        <div className="metric-value">
          {stats.win_rate !== null ? `${(stats.win_rate * 100).toFixed(2)}%` : '—'}
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-label">Profit Factor</div>
        <div className="metric-value">
          {stats.profit_factor !== null ? stats.profit_factor.toFixed(2) : '—'}
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-label">Max Drawdown</div>
        <div className="metric-value text-danger">
          {formatMoney(stats.max_drawdown)} USDT
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-label">Trades</div>
        <div className="metric-value">
          {stats.trades_count}
        </div>
      </div>
    </div>
  );
};
