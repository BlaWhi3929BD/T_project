import { useEffect, useMemo, useState } from 'react';

import { fetchFilterOptions, fetchStats, fetchTrades } from '../services/api';
import { DashboardFilters, FilterOptions, StatsResponse, TradeListResponse } from '../types/api';

interface DashboardData {
  options: FilterOptions;
  stats: StatsResponse | null;
  tradesData: TradeListResponse | null;
  statsLoading: boolean;
  tradesLoading: boolean;
  error: string | null;
}

const EMPTY_OPTIONS: FilterOptions = { symbols: [], strategies: [] };

export function useDashboardData(filters: DashboardFilters): DashboardData {
  const [options, setOptions] = useState<FilterOptions>(EMPTY_OPTIONS);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [tradesData, setTradesData] = useState<TradeListResponse | null>(null);
  const [statsError, setStatsError] = useState<string | null>(null);
  const [tradesError, setTradesError] = useState<string | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);
  const [tradesLoading, setTradesLoading] = useState(true);

  const filterKey = useMemo(
    () =>
      JSON.stringify({
        symbols: filters.symbols,
        strategies: filters.strategies,
        side: filters.side,
        dateFrom: filters.dateFrom,
        dateTo: filters.dateTo,
      }),
    [filters.symbols, filters.strategies, filters.side, filters.dateFrom, filters.dateTo],
  );
  const tradesKey = useMemo(
    () =>
      JSON.stringify({
        filterKey,
        sort: filters.sort,
        order: filters.order,
        page: filters.page,
        pageSize: filters.pageSize,
      }),
    [filterKey, filters.sort, filters.order, filters.page, filters.pageSize],
  );

  useEffect(() => {
    const controller = new AbortController();
    setStatsLoading(true);
    setStatsError(null);
    setStats(null);

    fetchStats(filters, controller.signal)
      .then((nextStats) => {
        if (!controller.signal.aborted) setStats(nextStats);
      })
      .catch((requestError: unknown) => {
        if (requestError instanceof Error && requestError.name === 'AbortError') return;
        if (!controller.signal.aborted) {
          setStatsError('Ошибка при загрузке статистики');
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setStatsLoading(false);
      });

    return () => controller.abort();
  }, [filterKey]);

  useEffect(() => {
    const controller = new AbortController();
    setTradesLoading(true);
    setTradesError(null);
    setTradesData(null);

    fetchTrades(filters, controller.signal)
      .then((nextTrades) => {
        if (!controller.signal.aborted) setTradesData(nextTrades);
      })
      .catch((requestError: unknown) => {
        if (requestError instanceof Error && requestError.name === 'AbortError') return;
        if (!controller.signal.aborted) {
          setTradesError('Ошибка при загрузке списка сделок');
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setTradesLoading(false);
      });

    return () => controller.abort();
  }, [tradesKey]);

  useEffect(() => {
    const controller = new AbortController();

    fetchFilterOptions(controller.signal)
      .then((nextOptions) => {
        if (!controller.signal.aborted) setOptions(nextOptions);
      })
      .catch((requestError: unknown) => {
        if (requestError instanceof Error && requestError.name === 'AbortError') return;
        if (!controller.signal.aborted) {
          setTradesError('Ошибка при загрузке списков фильтров');
        }
      });

    return () => controller.abort();
  }, []);

  return {
    options,
    stats,
    tradesData,
    statsLoading,
    tradesLoading,
    error: statsError ?? tradesError,
  };
}
