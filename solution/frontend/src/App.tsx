/**
 * @file App.tsx
 * Главный компонент приложения Дашборд аналитики по сделкам.
 * Управляет состоянием, загрузкой данных и компоновкой разделов.
 */

import { useEffect, useState, useRef } from 'react';
import { useDashboardFilters } from './hooks/useDashboardFilters';
import { fetchFilterOptions, fetchStats, fetchTrades } from './services/api';
import { FilterOptions, StatsResponse, TradeListResponse } from './types/api';

// Компоненты
import { Metrics } from './components/Metrics';
import { FiltersPanel } from './components/FiltersPanel';
import { EquityChart } from './components/EquityChart';
import { TradesTable } from './components/TradesTable';

function App() {
  const { filters, updateFilters } = useDashboardFilters();
  
  // Состояние данных
  const [options, setOptions] = useState<FilterOptions>({ symbols: [], strategies: [] });
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [tradesData, setTradesData] = useState<TradeListResponse | null>(null);
  
  // Состояние UI
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Рефы для хранения текущих контроллеров запросов (отмена при смене фильтров)
  const statsAbortController = useRef<AbortController | null>(null);
  const tradesAbortController = useRef<AbortController | null>(null);

  /**
   * Первичная загрузка доступных опций для фильтров
   */
  useEffect(() => {
    fetchFilterOptions()
      .then(setOptions)
      .catch(err => console.error("Failed to load filter options", err));
  }, []);

  /**
   * Загрузка статистики и списка сделок при изменении фильтров.
   * Реализует требование 7: "на экране всегда данные, соответствующие текущим фильтрам".
   */
  useEffect(() => {
    setLoading(true);
    setError(null);

    // Отменяем предыдущие запросы, если они еще не завершились
    if (statsAbortController.current) statsAbortController.current.abort();
    if (tradesAbortController.current) tradesAbortController.current.abort();

    statsAbortController.current = new AbortController();
    tradesAbortController.current = new AbortController();

    // Загружаем статистику (не зависит от пагинации, только от фильтров)
    fetchStats(filters, statsAbortController.current.signal)
      .then(setStats)
      .catch(err => {
        if (err.name !== 'AbortError') {
          setError('Ошибка при загрузке статистики');
          console.error(err);
        }
      });

    // Загружаем список сделок (зависит от фильтров, сортировки и пагинации)
    fetchTrades(filters, tradesAbortController.current.signal)
      .then(setTradesData)
      .catch(err => {
        if (err.name !== 'AbortError') {
          setError('Ошибка при загрузке списка сделок');
          console.error(err);
        }
      })
      .finally(() => {
        if (!tradesAbortController.current?.signal.aborted) {
          setLoading(false);
        }
      });

    return () => {
      statsAbortController.current?.abort();
      tradesAbortController.current?.abort();
    };
  }, [
    // Список зависимостей включает все поля фильтров
    filters.symbols,
    filters.strategies,
    filters.side,
    filters.dateFrom,
    filters.dateTo,
    filters.sort,
    filters.order,
    filters.page,
    filters.pageSize
  ]);

  return (
    <div className="container">
      <header style={{ marginBottom: '2rem' }}>
        <h1 style={{ margin: 0, color: '#111827' }}>Analytics Dashboard</h1>
        <p style={{ color: '#6b7280', margin: '0.5rem 0 0 0' }}>
          Аналитика торговых стратегий и мониторинг сделок
        </p>
      </header>

      {/* 1. Панель фильтров */}
      <FiltersPanel 
        filters={filters} 
        options={options} 
        onFilterChange={updateFilters} 
      />

      {error && (
        <div className="card" style={{ color: '#ef4444', borderColor: '#fecaca', background: '#fef2f2' }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* 2. Строка метрик */}
      <Metrics stats={stats} />

      {/* 3. График Equity */}
      {stats && stats.equity_curve.length > 0 ? (
        <EquityChart data={stats.equity_curve} />
      ) : (
        <div className="card" style={{ height: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#6b7280' }}>
          {loading ? 'Загрузка графика...' : 'Нет данных для отображения графика'}
        </div>
      )}

      {/* 4. Таблица сделок */}
      <TradesTable 
        data={tradesData} 
        filters={filters} 
        onFilterChange={updateFilters} 
      />

      <footer style={{ marginTop: '3rem', paddingBottom: '2rem', textAlign: 'center', color: '#9ca3af', fontSize: '0.75rem' }}>
        &copy; 2024 Trades Dashboard. Asia/Almaty timezone used for all daily groupings.
      </footer>
    </div>
  );
}

export default App;
