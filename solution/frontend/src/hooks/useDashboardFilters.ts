/**
 * @file useDashboardFilters.ts
 * Пользовательский хук для управления состоянием фильтров, сортировки и пагинации.
 * Обеспечивает синхронизацию состояния с URL-параметрами (требование 6 задания).
 */

import { useState, useEffect, useCallback } from 'react';
import { DashboardFilters } from '../types/api';

export const DEFAULT_FILTERS: DashboardFilters = {
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

const SORT_VALUES = ['closed_at', 'pnl', 'symbol'] as const;
const ORDER_VALUES = ['asc', 'desc'] as const;

function oneOf<const T extends readonly string[]>(
  value: string | null,
  values: T,
  fallback: T[number],
): T[number] {
  return value && (values as readonly string[]).includes(value)
    ? (value as T[number])
    : fallback;
}

function positiveInteger(value: string | null, fallback: number, maximum?: number): number {
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed < 1 || (maximum !== undefined && parsed > maximum)) {
    return fallback;
  }
  return parsed;
}

/**
 * Хук для работы с фильтрами дашборда.
 * Читает начальное состояние из URL и обновляет URL при изменении состояния.
 */
export function useDashboardFilters() {
  const [filters, setFilters] = useState<DashboardFilters>(() => {
    // Инициализация состояния из параметров URL при первой загрузке
    const params = new URLSearchParams(window.location.search);
    
    return {
      symbols: params.getAll('symbol'),
      strategies: params.getAll('strategy'),
      side: oneOf(params.get('side'), ['', 'long', 'short'] as const, ''),
      dateFrom: params.get('date_from') || '',
      dateTo: params.get('date_to') || '',
      sort: oneOf(params.get('sort'), SORT_VALUES, 'closed_at'),
      order: oneOf(params.get('order'), ORDER_VALUES, 'desc'),
      page: positiveInteger(params.get('page'), 1),
      pageSize: positiveInteger(params.get('page_size'), 50, 200),
    };
  });

  // Синхронизация состояния фильтров с URL-адресом
  useEffect(() => {
    const params = new URLSearchParams();
    
    filters.symbols.forEach(s => params.append('symbol', s));
    filters.strategies.forEach(s => params.append('strategy', s));
    if (filters.side) params.set('side', filters.side);
    if (filters.dateFrom) params.set('date_from', filters.dateFrom);
    if (filters.dateTo) params.set('date_to', filters.dateTo);
    
    params.set('sort', filters.sort);
    params.set('order', filters.order);
    params.set('page', filters.page.toString());
    params.set('page_size', filters.pageSize.toString());

    const newUrl = `${window.location.pathname}?${params.toString()}`;
    // Используем pushState, чтобы можно было пользоваться кнопками "Назад"/"Вперед" в браузере
    window.history.pushState({}, '', newUrl);
  }, [filters]);

  /**
   * Универсальная функция обновления фильтров.
   * Если меняются ключевые фильтры (не страница), сбрасывает страницу на 1.
   */
  const updateFilters = useCallback((updates: Partial<DashboardFilters>) => {
    setFilters((prev) => {
      const next = { ...prev, ...updates };
      
      // Если изменилось что-то кроме номера страницы, сбрасываем на первую
      const isOnlyPageChange = Object.keys(updates).length === 1 && 'page' in updates;
      if (!isOnlyPageChange) {
        next.page = 1;
      }
      
      return next;
    });
  }, []);

  return {
    filters,
    updateFilters,
  };
}
