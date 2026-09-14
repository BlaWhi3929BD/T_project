/**
 * @file TradesTable.tsx
 * Компонент таблицы сделок с пагинацией и сортировкой.
 */

import React from 'react';
import { Trade, TradeListResponse, DashboardFilters } from '../types/api';
import { formatMoney, parseMoney } from '../utils/formatMoney';

interface TradesTableProps {
  data: TradeListResponse | null;
  filters: DashboardFilters;
  onFilterChange: (updates: Partial<DashboardFilters>) => void;
}

/**
 * Отображает таблицу сделок.
 * Поддерживает смену сортировки при клике на заголовки Symbol, PnL, Closed At.
 */
export const TradesTable: React.FC<TradesTableProps> = ({ data, filters, onFilterChange }) => {
  if (!data) return <div className="card">Загрузка таблицы...</div>;

  const handleSort = (field: 'symbol' | 'pnl' | 'closed_at') => {
    if (filters.sort === field) {
      // Если кликнули на то же поле, меняем направление
      onFilterChange({ order: filters.order === 'asc' ? 'desc' : 'asc' });
    } else {
      // Если новое поле, ставим его и сбрасываем на desc
      onFilterChange({ sort: field, order: 'desc' });
    }
  };

  const getSortIcon = (field: string) => {
    if (filters.sort !== field) return '↕️';
    return filters.order === 'asc' ? '↑' : '↓';
  };

  const totalPages = Math.ceil(data.total / filters.pageSize);

  return (
    <div className="card">
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th onClick={() => handleSort('symbol')}>Symbol {getSortIcon('symbol')}</th>
              <th>Strategy</th>
              <th>Side</th>
              <th onClick={() => handleSort('closed_at')}>Closed At {getSortIcon('closed_at')}</th>
              <th>Qty</th>
              <th>Entry</th>
              <th>Exit</th>
              <th onClick={() => handleSort('pnl')}>PnL {getSortIcon('pnl')}</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((trade: Trade) => (
              <tr key={trade.id}>
                <td>{trade.id}</td>
                <td><strong>{trade.symbol}</strong></td>
                <td>{trade.strategy}</td>
                <td>
                  <span style={{ color: trade.side === 'long' ? '#10b981' : '#3b82f6', fontWeight: 600 }}>
                    {trade.side.toUpperCase()}
                  </span>
                </td>
                <td>{new Date(trade.closed_at).toLocaleString()}</td>
                <td>{trade.qty}</td>
                <td>{formatMoney(trade.entry_price)}</td>
                <td>{formatMoney(trade.exit_price)}</td>
                <td className={parseMoney(trade.pnl) >= 0 ? 'text-success' : 'text-danger'}>
                  {formatMoney(trade.pnl)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Пагинация */}
      <div className="pagination">
        <button 
          disabled={filters.page <= 1} 
          onClick={() => onFilterChange({ page: filters.page - 1 })}
        >
          Previous
        </button>
        
        <span>
          Page <strong>{filters.page}</strong> of {totalPages || 1} 
          <small style={{ marginLeft: '1rem', color: '#6b7280' }}>
            (Total trades: {data.total})
          </small>
        </span>

        <button 
          disabled={filters.page >= totalPages} 
          onClick={() => onFilterChange({ page: filters.page + 1 })}
        >
          Next
        </button>
      </div>
    </div>
  );
};
