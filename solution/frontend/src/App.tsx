import { useDashboardFilters } from './hooks/useDashboardFilters';
import { useDashboardData } from './hooks/useDashboardData';

import { EquityChart } from './components/EquityChart';
import { FiltersPanel } from './components/FiltersPanel';
import { Metrics } from './components/Metrics';
import { TradesTable } from './components/TradesTable';

function App() {
  const { filters, updateFilters } = useDashboardFilters();
  const { options, stats, tradesData, statsLoading, tradesLoading, error } = useDashboardData(filters);
  const loading = statsLoading || tradesLoading;

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
