export interface Trade {
  id: number;
  symbol: string;
  strategy: string;
  side: 'long' | 'short';
  opened_at: string;
  closed_at: string;
  qty: string;
  entry_price: string;
  exit_price: string;
  fee: string;
  pnl: string;
}

export interface Stats {
  trades_count: number;
  wins: number;
  losses: number;
  breakeven: number;
  net_pnl: string;
  win_rate: number | null;
  profit_factor: number | null;
  max_drawdown: string;
  equity_curve: Array<{ date: string; day_pnl: string; cum_pnl: string }>;
}
