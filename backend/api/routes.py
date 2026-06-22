from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import numpy as np

from backend.database import get_db
from backend.config import get_settings
from backend.models.trade import Trade, TradeStatus
from backend.models.signal import Signal
from backend.api.schemas import (
    TradeOut, SignalOut, PerformanceStats,
    OHLCVCandle, TickerOut,
)
from backend.services.exchange import fetch_ticker
from backend.services.data_fetcher import fetch_and_store_ohlcv, get_ohlcv_from_db
from backend.ml.trainer import train_model, model_exists
from backend.ml.predictor import predict_signal

router   = APIRouter()
settings = get_settings()


# ── Health check ──────────────────────────────────────────
@router.get("/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME}

# ── Ticker ────────────────────────────────────────────────
@router.get("/ticker", response_model=TickerOut)
async def get_ticker(symbol: str = None):
    """Ambil harga ticker terkini dari exchange."""
    try:
        return await fetch_ticker(symbol)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Exchange error: {str(e)}")

# ── OHLCV ─────────────────────────────────────────────────
@router.get("/ohlcv", response_model=List[OHLCVCandle])
def get_ohlcv(
    symbol:    str  = None,
    timeframe: str  = None,
    limit:     int  = 200,
    refresh:   bool = False,
    db:        Session = Depends(get_db),
):
    """
    Ambil data candlestick OHLCV.
    Tambah ?refresh=true untuk fetch ulang dari exchange.
    """
    try:
        if refresh:
            return fetch_and_store_ohlcv(db, symbol, timeframe, limit)
        cached = get_ohlcv_from_db(db, symbol, timeframe, limit)
        if cached:
            return cached
        return fetch_and_store_ohlcv(db, symbol, timeframe, limit)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Exchange error: {str(e)}")


# ── Trades ────────────────────────────────────────────────
@router.get("/trades", response_model=List[TradeOut])
def get_trades(limit: int = 50, db: Session = Depends(get_db)):
    """Riwayat semua trade, terbaru duluan."""
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
    """Riwayat sinyal AI, terbaru duluan."""
    return db.query(Signal).order_by(Signal.created_at.desc()).limit(limit).all()


# ── Performance stats ─────────────────────────────────────
@router.get("/performance", response_model=PerformanceStats)
def get_performance(db: Session = Depends(get_db)):
    """Statistik performa: Sharpe, drawdown, win rate, PnL."""
    closed = db.query(Trade).filter(Trade.status == TradeStatus.CLOSED).all()

    if not closed:
        return PerformanceStats(
            total_trades=0, win_rate=0.0, total_pnl=0.0,
            total_pnl_pct=0.0, avg_pnl_pct=0.0,
            max_drawdown=0.0, sharpe_ratio=0.0,
        )

    wins    = [t for t in closed if (t.pnl or 0) > 0]
    pnls    = [t.pnl_pct or 0 for t in closed]
    pnl_arr = np.array(pnls)

    sharpe = (
        float(pnl_arr.mean() / pnl_arr.std() * (252 ** 0.5))
        if pnl_arr.std() > 0 else 0.0
    )

    cumulative   = np.cumsum(pnl_arr)
    running_max  = np.maximum.accumulate(cumulative)
    max_drawdown = float((cumulative - running_max).min())

    return PerformanceStats(
        total_trades  = len(closed),
        win_rate      = len(wins) / len(closed),
        total_pnl     = sum(t.pnl or 0 for t in closed),
        total_pnl_pct = float(pnl_arr.sum()),
        avg_pnl_pct   = float(pnl_arr.mean()),
        max_drawdown  = max_drawdown,
        sharpe_ratio  = round(sharpe, 2),
    )


# ── ML ────────────────────────────────────────────────────
@router.post("/ml/train")
def train(
    symbol:    str = None,
    timeframe: str = None,
    limit:     int = 1000,
    db:        Session = Depends(get_db),
):
    """Train model AI dengan data historis. Rekomendasikan limit >= 500."""
    try:
        candles = fetch_and_store_ohlcv(db, symbol, timeframe, limit)
        return train_model(candles)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training error: {str(e)}")


@router.get("/ml/predict")
def predict(
    symbol:    str = None,
    timeframe: str = None,
    db:        Session = Depends(get_db),
):
    """Generate sinyal BUY/SELL/HOLD dari model AI."""
    try:
        candles = get_ohlcv_from_db(db, symbol, timeframe, limit=200)
        if not candles:
            candles = fetch_and_store_ohlcv(db, symbol, timeframe, 200)
        return predict_signal(candles)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@router.get("/ml/status")
def ml_status():
    """Cek apakah model sudah ditraining."""
    exists = model_exists()
    return {
        "model_exists": exists,
        "message": "Model siap" if exists else "Belum ditraining. POST /api/ml/train dulu.",
    }


# ── Bot control ───────────────────────────────────────────
@router.get("/bot/status")
def get_bot_status():
    """Status bot: running/stopped, paper/live, kapital saat ini."""
    from backend.services.bot_engine import bot
    return bot.get_status()


@router.post("/bot/start")
async def start_bot(paper: bool = True):
    """Mulai bot trading."""
    from backend.services.bot_engine import bot
    result = bot.start(paper=paper)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/bot/stop")
async def stop_bot():
    """Hentikan bot trading."""
    from backend.services.bot_engine import bot
    return bot.stop()