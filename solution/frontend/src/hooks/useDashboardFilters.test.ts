import { act, renderHook } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { DEFAULT_FILTERS, useDashboardFilters } from './useDashboardFilters';

afterEach(() => {
  window.history.replaceState({}, '', '/');
});

describe('useDashboardFilters', () => {
  it('restores valid filter state from the URL', () => {
    window.history.replaceState(
      {},
      '',
      '/?symbol=BTCUSDT&strategy=momentum_v1&side=short&date_from=2024-01-01&sort=pnl&order=asc&page=3&page_size=25',
    );

    const { result } = renderHook(() => useDashboardFilters());

    expect(result.current.filters).toEqual({
      ...DEFAULT_FILTERS,
      symbols: ['BTCUSDT'],
      strategies: ['momentum_v1'],
      side: 'short',
      dateFrom: '2024-01-01',
      sort: 'pnl',
      order: 'asc',
      page: 3,
      pageSize: 25,
    });
  });

  it('falls back for invalid URL values', () => {
    window.history.replaceState({}, '', '/?side=invalid&sort=other&order=other&page=0&page_size=201');

    const { result } = renderHook(() => useDashboardFilters());

    expect(result.current.filters).toMatchObject(DEFAULT_FILTERS);
  });

  it('resets page when a filter changes but preserves explicit page changes', () => {
    const { result } = renderHook(() => useDashboardFilters());

    act(() => result.current.updateFilters({ page: 4 }));
    expect(result.current.filters.page).toBe(4);

    act(() => result.current.updateFilters({ side: 'long' }));
    expect(result.current.filters).toMatchObject({ side: 'long', page: 1 });
  });

  it('serializes state into the URL', () => {
    const { result } = renderHook(() => useDashboardFilters());

    act(() => {
      result.current.updateFilters({
        symbols: ['ETHUSDT'],
        order: 'asc',
      });
    });
    act(() => result.current.updateFilters({ page: 2 }));

    expect(window.location.search).toContain('symbol=ETHUSDT');
    expect(window.location.search).toContain('order=asc');
    expect(window.location.search).toContain('page=2');
  });
});
