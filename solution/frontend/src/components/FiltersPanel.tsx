/**
 * @file FiltersPanel.tsx
 * Компонент панели фильтров.
 * Позволяет выбирать символы, стратегии, сторону сделки и диапазон дат.
 */

import React from 'react';
import { DashboardFilters, FilterOptions } from '../types/api';

function parseSide(value: string): DashboardFilters['side'] {
  return value === 'long' || value === 'short' ? value : '';
}

interface FiltersPanelProps {
  filters: DashboardFilters;
  options: FilterOptions;
  onFilterChange: (updates: Partial<DashboardFilters>) => void;
}

/**
 * Панель фильтров с мультивыбором для символов и стратегий (через зажатый Ctrl/Cmd).
 */
export const FiltersPanel: React.FC<FiltersPanelProps> = ({ filters, options, onFilterChange }) => {
  
  const handleMultiSelectChange = (
    e: React.ChangeEvent<HTMLSelectElement>, 
    field: 'symbols' | 'strategies'
  ) => {
    const values = Array.from(e.target.selectedOptions, option => option.value);
    onFilterChange({ [field]: values });
  };

  return (
    <div className="card">
      <div className="filters-grid">
        {/* Фильтр по символам */}
        <div className="filter-group">
          <label>Symbols (Ctrl+Click)</label>
          <select 
            multiple 
            value={filters.symbols} 
            onChange={(e) => handleMultiSelectChange(e, 'symbols')}
            style={{ height: '80px' }}
          >
            {options.symbols.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>

        {/* Фильтр по стратегиям */}
        <div className="filter-group">
          <label>Strategies (Ctrl+Click)</label>
          <select 
            multiple 
            value={filters.strategies} 
            onChange={(e) => handleMultiSelectChange(e, 'strategies')}
            style={{ height: '80px' }}
          >
            {options.strategies.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>

        {/* Фильтр по стороне сделки */}
        <div className="filter-group">
          <label>Side</label>
          <select 
            value={filters.side} 
            onChange={(e) => onFilterChange({ side: parseSide(e.target.value) })}
          >
            <option value="">All Sides</option>
            <option value="long">Long</option>
            <option value="short">Short</option>
          </select>
        </div>

        {/* Фильтр по датам */}
        <div className="filter-group">
          <label>Date From</label>
          <input 
            type="date" 
            value={filters.dateFrom} 
            onChange={(e) => onFilterChange({ dateFrom: e.target.value })} 
          />
        </div>
        <div className="filter-group">
          <label>Date To</label>
          <input 
            type="date" 
            value={filters.dateTo} 
            onChange={(e) => onFilterChange({ dateTo: e.target.value })} 
          />
        </div>
      </div>
      
      {/* Кнопка сброса */}
      <div style={{ marginTop: '1rem', textAlign: 'right' }}>
        <button onClick={() => window.location.href = window.location.pathname}>
          Reset All Filters
        </button>
      </div>
    </div>
  );
};
