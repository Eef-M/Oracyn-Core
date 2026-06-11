// ── Bot ───────────────────────────────────────────────────
export interface BotStatus {
  running: boolean
  is_paper: boolean
  symbol: string
  timeframe: string
  capital: number
}

// ── Market ────────────────────────────────────────────────
export interface Ticker {
  symbol: string
  last: number
  bid: number
  ask: number
  high: number
  low: number
  volume: number
  change_pct: number
  timestamp: string
}

export interface OHLCVCandle {
  timestamp: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

// ── Signal ────────────────────────────────────────────────
export type SignalType = 'BUY' | 'SELL' | 'HOLD'

export interface Signal {
  id: number
  symbol: string
  signal: SignalType
  confidence: number
  price: number
  rsi: number | null
  macd: number | null
  created_at: string
}

// ── Trade ─────────────────────────────────────────────────
export type TradeAction = 'BUY' | 'SELL'
export type TradeStatus = 'OPEN' | 'CLOSED'

export interface Trade {
  id: number
  symbol: string
  action: TradeAction
  status: TradeStatus
  entry_price: number
  exit_price: number | null
  quantity: number
  pnl: number | null
  pnl_pct: number | null
  stop_loss: number | null
  is_paper: boolean
  opened_at: string
  closed_at: string | null
}

// ── Performance ───────────────────────────────────────────
export interface PerformanceStats {
  total_trades: number
  win_rate: number
  total_pnl: number
  total_pnl_pct: number
  avg_pnl_pct: number
  max_drawdown: number
  sharpe_ratio: number
}

// ── WebSocket ─────────────────────────────────────────────
export type LiveUpdate =
  | {
    type: 'live_update'
    symbol: string
    price: number
    change_pct: number
    high: number
    low: number
    volume: number
    bot: {
      running: boolean
      is_paper: boolean
      capital: number
    }
    timestamp: string
  }
  | {
    type: 'error'
    message: string
  }