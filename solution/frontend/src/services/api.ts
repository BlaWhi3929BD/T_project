/**
 * @file api.ts
 * Сервисные функции для взаимодействия с HTTP API бэкенда FastAPI.
 * Поддерживает отмену устаревших запросов через AbortSignal.
 */

import { DashboardFilters, FilterOptions, StatsResponse, TradeListResponse } from '../types/api';

/**
 * Формирует общие query-параметры фильтрации на основе объекта фильтров DashboardFilters.
 * 
 * @param filters Текущие настройки фильтрации
 * @returns Экземпляр URLSearchParams с правильно отформатированными параметрами
 */
function buildFilterQueryParams(filters: DashboardFilters): URLSearchParams {
  const params = new URLSearchParams();

  // Добавляем повторяемые параметры для символов (?symbol=BTCUSDT&symbol=ETHUSDT)
  filters.symbols.forEach((sym) => {
    if (sym) params.append('symbol', sym);
  });

  // Добавляем повторяемые параметры для стратегий
  filters.strategies.forEach((strat) => {
    if (strat) params.append('strategy', strat);
  });

  // Фильтр по стороне сделки (long / short)
  if (filters.side) {
    params.append('side', filters.side);
  }

  // Фильтр по диапазону дат
  if (filters.dateFrom) {
    params.append('date_from', filters.dateFrom);
  }
  if (filters.dateTo) {
    params.append('date_to', filters.dateTo);
  }

  return params;
}

/**
 * Запрашивает список доступных опций фильтрации (символы и стратегии).
 * 
 * @param signal AbortSignal для возможности отмены запроса
 * @returns Обещание с опциями фильтров
 */
export async function fetchFilterOptions(signal?: AbortSignal): Promise<FilterOptions> {
  const response = await fetch('/api/filters/options', { signal });
  if (!response.ok) {
    throw new Error(`Ошибка загрузки списков фильтров: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Запрашивает статистические метрики и данные для графика по текущим фильтрам.
 * 
 * @param filters Текущие фильтры
 * @param signal AbortSignal для возможности отмены запроса при быстрой смене фильтров
 * @returns Обещание со статистикой и точками для графика
 */
export async function fetchStats(
  filters: DashboardFilters,
  signal?: AbortSignal
): Promise<StatsResponse> {
  const params = buildFilterQueryParams(filters);
  const response = await fetch(`/api/stats?${params.toString()}`, { signal });

  if (!response.ok) {
    throw new Error(`Ошибка загрузки статистики: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Запрашивает пагинированный список сделок с учетом фильтров, сортировки и пагинации.
 * 
 * @param filters Текущие фильтры, параметры сортировки и страница
 * @param signal AbortSignal для возможности отмены запроса при переключении страниц/фильтров
 * @returns Обещание с объектом, содержащим список сделок и общую статистику пагинации
 */
export async function fetchTrades(
  filters: DashboardFilters,
  signal?: AbortSignal
): Promise<TradeListResponse> {
  const params = buildFilterQueryParams(filters);

  // Добавляем параметры сортировки и пагинации
  params.append('sort', filters.sort);
  params.append('order', filters.order);
  params.append('page', filters.page.toString());
  params.append('page_size', filters.pageSize.toString());

  const response = await fetch(`/api/trades?${params.toString()}`, { signal });

  if (!response.ok) {
    throw new Error(`Ошибка загрузки списка сделок: ${response.statusText}`);
  }

  return response.json();
}
