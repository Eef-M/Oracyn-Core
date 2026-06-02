from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime
 
from backend.database import get_db
from backend.config import get_settings
from backend.models.trade import Trade, TradeStatus
from backend.models.signal import Signal
from backend.api.schemas import TradeOut, SignalOut, PerformanceStats, BotStatus, OHLCVCandle, TickerOut
from backend.services.exchange import fetch_ticker as exchange_fetch_ticker
from backend.services.data_fetcher import fetch_and_store_ohlcv, get_ohlcv_from_db

router = APIRouter()
settings = get_settings()
 
_bot_start_time: datetime | None = None
_bot_running: bool = False

# ── Health check ──────────────────────────────────────────
@router.get("/health")
def health():
  return {"status": "ok", "app_name": settings.APP_NAME}

# ── Bot control ───────────────────────────────────────────
@router.get("/bot/status", response_model=BotStatus)
def get_bot_status():
  global _bot_running, _bot_start_time
  uptime = None
  if _bot_start_time and _bot_running:
    uptime = int((datetime.utcnow() - _bot_start_time).total_seconds())
  return BotStatus(
    running=_bot_running,
    symbol=settings.SYMBOL,
    timeframe=settings.TIMEFRAME,
    is_paper=True,
    uptime_sec=uptime,
  )

@router.post("/bot/start")
def start_bot():
  global _bot_running, _bot_start_time
  if _bot_running:
    raise HTTPException(status_code=400, detail="Bot is already running")
  _bot_running = True
  _bot_start_time = datetime.utcnow()
  return {"message": "Bot dimulai", "started_at": _bot_start_time}

@router.post("/bot/stop")
def stop_bot():
  global _bot_running, _bot_start_time
  if not _bot_running:
    raise HTTPException(status_code=400, detail="Bot is not running")
  _bot_running = False
  _bot_start_time = None
  return {"message": "Bot Stopped"}

# ── Trades ────────────────────────────────────────────────
@router.get("/trades", response_model=List[TradeOut])
def get_trades(limit: int = 50, db: Session = Depends(get_db)):
  return db.query(Trade).order_by(Trade.opened_at.desc()).limit(limit).all()

@router.get("/trades/{trade_id}", response_model=TradeOut)
def get_trade(trade_id: int, db: Session = Depends(get_db)):
  trade = db.query(Trade).filter(Trade.id == trade_id).first()
  if not trade:
    raise HTTPException(status_code=404, detail="Trade tidak ditemukan")
  return trade

# ── Signals ───────────────────────────────────────────────
@router.get("/signals", response_model=List[SignalOut])
def get_signals(limit: int = 20, db: Session = Depends(get_db)):
  return db.query(Signal).order_by(Signal.created_at.desc()).limit(limit).all()

# ── Performance stats ─────────────────────────────────────
@router.get("/performance", response_model=PerformanceStats)
def get_performance(db: Session = Depends(get_db)):
  closed = db.query(Trade).filter(Trade.status == TradeStatus.CLOSED).all()

  if not closed:
      return PerformanceStats(
        total_trades=0, win_rate=0.0, total_pnl=0.0,
        total_pnl_pct=0.0, avg_pnl_pct=0.0,
        max_drawdown=0.0, sharpe_ratio=0.0,
      )

  wins = [t for t in closed if (t.pnl or 0) > 0]
  pnls = [t.pnl_pct or 0 for t in closed]

  import numpy as np
  pnl_arr = np.array(pnls)
  sharpe = (pnl_arr.mean() / pnl_arr.std() * (252 ** 0.5)) if pnl_arr.std() > 0 else 0.0

  cumulative = np.cumsum(pnl_arr)
  running_max = np.maximum.accumulate(cumulative)
  drawdown = cumulative - running_max
  max_drawdown = float(drawdown.min())

  return PerformanceStats(
    total_trades=len(closed),
    win_rate=len(wins) / len(closed),
    total_pnl=sum(t.pnl or 0 for t in closed),
    total_pnl_pct=sum(pnls),
    avg_pnl_pct=float(pnl_arr.mean()),
    max_drawdown=max_drawdown,
    sharpe_ratio=round(sharpe, 2),
  )

# ── Ticker ────────────────────────────────────────────────
@router.get("/ticker", response_model=TickerOut)
def get_ticker(symbol: str = None):
  """
  Ambil harga ticker terkini langsung dari Binance.
  Contoh: GET /api/ticker?symbol=ETH/USDT
  """
  try:
    return exchange_fetch_ticker(symbol)
  except Exception as e:
    raise HTTPException(status_code=502, detail=f"Exchange error: {str(e)}")

# ── OHLCV ─────────────────────────────────────────────────
@router.get("/ohlcv", response_model=List[OHLCVCandle])
def get_ohlcv(
  symbol:    str = None,
  timeframe: str = None,
  limit:     int = 200,
  refresh:   bool = False,
  db:        Session = Depends(get_db),
):
  """
  Ambil data candlestick OHLCV.

  - Secara default ambil dari database (cepat).
  - Tambahkan ?refresh=true untuk fetch ulang dari Binance dan update DB.
  - Contoh: GET /api/ohlcv?symbol=BTC/USDT&timeframe=1h&limit=100
  """
  try:
    if refresh:
      return fetch_and_store_ohlcv(db, symbol, timeframe, limit)

    # Coba dari DB dulu
    cached = get_ohlcv_from_db(db, symbol, timeframe, limit)
    if cached:
      return cached

    # Kalau DB kosong, fetch dari Binance dan simpan
    return fetch_and_store_ohlcv(db, symbol, timeframe, limit)

  except Exception as e:
    raise HTTPException(status_code=502, detail=f"Exchange error: {str(e)}")
