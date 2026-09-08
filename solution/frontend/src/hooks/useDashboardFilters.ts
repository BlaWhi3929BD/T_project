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
      side: (params.get('side') as 'long' | 'short' | '') || '',
      dateFrom: params.get('date_from') || '',
      dateTo: params.get('date_to') || '',
      sort: (params.get('sort') as any) || 'closed_at',
      order: (params.get('order') as any) || 'desc',
      page: parseInt(params.get('page') || '1', 10),
      pageSize: parseInt(params.get('page_size') || '50', 10),
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
