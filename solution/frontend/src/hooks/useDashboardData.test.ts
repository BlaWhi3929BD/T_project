import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { fetchFilterOptions, fetchStats, fetchTrades } from '../services/api';
import { DashboardFilters } from '../types/api';
import { useDashboardData } from './useDashboardData';

vi.mock('../services/api', () => ({
  fetchFilterOptions: vi.fn(),
  fetchStats: vi.fn(),
  fetchTrades: vi.fn(),
}));

const filters: DashboardFilters = {
  symbols: [],
  strategies: [],
  side: '',
  dateFrom: '',
  dateTo: '',
  sort: 'closed_at',
  order: 'desc',
  page: 1,
  pageSize: 50,
};

const stats = {
  trades_count: 1,
  wins: 1,
  losses: 0,
  breakeven: 0,
  net_pnl: '1.00',
  gross_profit: '1.00',
  gross_loss: '0.00',
  win_rate: 1,
  profit_factor: null,
  avg_win: '1.00',
  avg_loss: null,
  best_trade: '1.00',
  worst_trade: '1.00',
  max_drawdown: '0.00',
  equity_curve: [],
};

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(fetchFilterOptions).mockResolvedValue({ symbols: [], strategies: [] });
  vi.mocked(fetchTrades).mockResolvedValue({ items: [], page: 1, page_size: 50, total: 0 });
});

describe('useDashboardData', () => {
  it('loads stats and trades independently and reports loading completion', async () => {
    vi.mocked(fetchStats).mockResolvedValue(stats);

    const { result } = renderHook(() => useDashboardData(filters));

    expect(result.current.statsLoading).toBe(true);
    expect(result.current.tradesLoading).toBe(true);

    await waitFor(() => expect(result.current.stats).toEqual(stats));
    await waitFor(() => expect(result.current.statsLoading).toBe(false));
    await waitFor(() => expect(result.current.tradesLoading).toBe(false));
    expect(result.current.error).toBeNull();
  });

  it('ignores an aborted request and exposes non-abort errors', async () => {
    let rejectStats: ((error: unknown) => void) | undefined;
    vi.mocked(fetchStats).mockImplementation(
      () =>
        new Promise((_, reject) => {
          rejectStats = reject;
        }),
    );

    const { result } = renderHook(() => useDashboardData(filters));
    act(() => rejectStats?.(new Error('request failed')));

    await waitFor(() => expect(result.current.error).toBe('Ошибка при загрузке статистики'));
  });
});
