from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from backend.models.trade import TradeAction, TradeStatus
from backend.models.signal import SignalType


# ── Trade schemas ──────────────────────────────────────────
class TradeOut(BaseModel):
  id:          int
  symbol:      str
  action:      TradeAction
  status:      TradeStatus
  entry_price: float
  exit_price:  Optional[float]
  quantity:    float
  pnl:         Optional[float]
  pnl_pct:     Optional[float]
  stop_loss:   Optional[float]
  is_paper:    bool
  opened_at:   datetime
  closed_at:   Optional[datetime]

  class Config:
      from_attributes = True


# ── Signal schemas ─────────────────────────────────────────
class SignalOut(BaseModel):
  id:         int
  symbol:     str
  signal:     SignalType
  confidence: float
  price:      float
  rsi:        Optional[float]
  macd:       Optional[float]
  created_at: datetime

  class Config:
      from_attributes = True


# ── Stats schemas ──────────────────────────────────────────
class PerformanceStats(BaseModel):
  total_trades:   int
  win_rate:       float
  total_pnl:      float
  total_pnl_pct:  float
  avg_pnl_pct:    float
  max_drawdown:   float
  sharpe_ratio:   float


# ── Bot control schemas ───────────────────────────────────
class BotStatus(BaseModel):
  running:    bool
  symbol:     str
  timeframe:  str
  is_paper:   bool
  uptime_sec: Optional[int]


# ── WebSocket live data ───────────────────────────────────
class LiveData(BaseModel):
  symbol:     str
  price:      float
  signal:     Optional[str]
  confidence: Optional[float]
  timestamp:  datetime