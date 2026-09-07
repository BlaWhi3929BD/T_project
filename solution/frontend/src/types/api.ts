/**
 * @file api.ts
 * Этот файл содержит описания типов TypeScript для всех сущностей, 
 * передаваемых между бэкендом (FastAPI) и фронтендом (React).
 */

/**
 * Описывает одну торговую сделку.
 */
export interface Trade {
  /** Уникальный идентификатор сделки */
  id: number;
  /** Торговая пара/символ (например, BTCUSDT) */
  symbol: string;
  /** Торговая стратегия (например, momentum_v1) */
  strategy: string;
  /** Сторона сделки: "long" (покупка) или "short" (продажа) */
  side: 'long' | 'short';
  /** Время открытия сделки в формате ISO 8601 (UTC) */
  opened_at: string;
  /** Время закрытия сделки в формате ISO 8601 (UTC) */
  closed_at: string;
  /** Количество торгового актива (строка для сохранения точности) */
  qty: string;
  /** Цена входа в сделку */
  entry_price: string;
  /** Цена выхода из сделки */
  exit_price: string;
  /** Комиссия за сделку */
  fee: string;
  /** Итоговый финансовый результат (PnL) с учетом комиссии */
  pnl: string;
}

/**
 * Ответ эндпоинта GET /api/trades с поддержкой пагинации.
 */
export interface TradeListResponse {
  /** Список сделок на текущей странице */
  items: Trade[];
  /** Номер текущей страницы (начиная с 1) */
  page: number;
  /** Количество сделок на одной странице */
  page_size: number;
  /** Общее количество сделок, удовлетворяющих условиям фильтра */
  total: number;
}

/**
 * Точка на графике кривой накопленного PnL (equity curve).
 */
export interface EquityCurvePoint {
  /** Календарные сутки в формате YYYY-MM-DD (в часовом поясе Asia/Almaty) */
  date: string;
  /** Суммарный PnL за указанный день */
  day_pnl: string;
  /** Накопленный PnL к концу указанного дня */
  cum_pnl: string;
}

/**
 * Ответ эндпоинта GET /api/stats со всеми агрегированными метриками.
 */
export interface StatsResponse {
  /** Общее количество сделок в отфильтрованной выборке */
  trades_count: number;
  /** Количество прибыльных сделок (pnl > 0) */
  wins: number;
  /** Количество убыточных сделок (pnl < 0) */
  losses: number;
  /** Количество безубыточных сделок (pnl == 0) */
  breakeven: number;
  /** Чистый суммарный результат всех сделок (в USDT) */
  net_pnl: string;
  /** Валовая прибыль (сумма всех прибылей) */
  gross_profit: string;
  /** Валовый убыток (абсолютная сумма всех убытков) */
  gross_loss: string;
  /** Процент прибыльных сделок (wins / trades_count) или null если сделок 0 */
  win_rate: number | null;
  /** Коэффициент прибыльности (gross_profit / gross_loss) или null */
  profit_factor: number | null;
  /** Средняя прибыль на одну прибыльную сделку или null */
  avg_win: string | null;
  /** Средний убыток на одну убыточную сделку или null */
  avg_loss: string | null;
  /** Результат лучшей сделки */
  best_trade: string;
  /** Результат худшей сделки */
  worst_trade: string;
  /** Максимальная просадка накопленного PnL */
  max_drawdown: string;
  /** Массив данных для построения графика накопленного результата */
  equity_curve: EquityCurvePoint[];
}

/**
 * Ответ эндпоинта GET /api/filters/options со списком доступных опций фильтрации.
 */
export interface FilterOptions {
  /** Доступные торговые символы */
  symbols: string[];
  /** Доступные торговые стратегии */
  strategies: string[];
}

/**
 * Текущие выбранные фильтры и параметры сортировки/пагинации в UI.
 */
export interface DashboardFilters {
  /** Выбранные символы (мультивыбор) */
  symbols: string[];
  /** Выбранные стратегии (мультивыбор) */
  strategies: string[];
  /** Выбранное направление сделки (long / short / все) */
  side: '' | 'long' | 'short';
  /** Начальная дата диапазона (YYYY-MM-DD) */
  dateFrom: string;
  /** Конечная дата диапазона (YYYY-MM-DD) */
  dateTo: string;
  /** Поле сортировки таблицы сделок */
  sort: 'closed_at' | 'pnl' | 'symbol';
  /** Направление сортировки таблицы сделок */
  order: 'asc' | 'desc';
  /** Номер текущей страницы таблицы */
  page: number;
  /** Количество записей на странице таблицы */
  pageSize: number;
}
