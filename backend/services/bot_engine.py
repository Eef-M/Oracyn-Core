import asyncio
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.config import get_settings
from backend.database import SessionLocal
from backend.models.trade import Trade, TradeAction, TradeStatus
from backend.models.signal import Signal, SignalType
from backend.services.exchange import fetch_ticker
from backend.services.data_fetcher import fetch_and_store_ohlcv
from backend.services.risk_manager import RiskManager
from backend.ml.predictor import predict_signal
from backend.ml.trainer import model_exists

settings = get_settings()

class BotEngine:
  def __init__(self):
    self.settings      = settings
    self.risk_manager  = RiskManager()
    self.is_running    = False
    self.is_paper      = True
    self.capital       = settings.INITIAL_CAPITAL
    self.tick_interval = 60
    self._task         = None

  def start(self, paper: bool = True):
    if self.is_running:
      return {"status": "already_running"}
    if not model_exists():
      return {"status": "error", "message": "Model belum ditraining. POST /api/ml/train dulu."}

    self.is_paper   = paper
    self.is_running = True
    self._task      = asyncio.create_task(self._run_loop())

    mode = "Paper Trading" if paper else "LIVE Trading"
    print(f"[BotEngine] ▶ {mode} dimulai — {settings.SYMBOL} {settings.TIMEFRAME}")
    return {"status": "started", "mode": mode, "symbol": settings.SYMBOL}

  def stop(self):
    if not self.is_running:
      return {"status": "not_running"}
    self.is_running = False
    if self._task:
      self._task.cancel()
      self._task = None
    print("[BotEngine] ■ Bot dihentikan")
    return {"status": "stopped"}

  def get_status(self) -> dict:
    return {
      "running":   self.is_running,
      "is_paper":  self.is_paper,
      "symbol":    settings.SYMBOL,
      "timeframe": settings.TIMEFRAME,
      "capital":   self.capital,
    }

  async def _run_loop(self):
    print(f"[BotEngine] Loop dimulai, interval: {self.tick_interval}s")
    while self.is_running:
      try:
        await self._tick()
      except asyncio.CancelledError:
        break
      except Exception as e:
        print(f"[BotEngine] Error pada tick: {e}")
      await asyncio.sleep(self.tick_interval)

  async def _tick(self):
    db = SessionLocal()
    try:
      ticker = await fetch_ticker(settings.SYMBOL)
      current_price = ticker["last"]
      print(f"[BotEngine] Tick — {settings.SYMBOL}: ${current_price:,.2f}")

      await self._check_open_positions(db, current_price)

      # Limit dinaikkan ke 250 — predictor butuh data cukup untuk EMA200
      candles = fetch_and_store_ohlcv(db, limit=250)
      result  = predict_signal(candles)

      signal            = result["signal"]
      confidence        = result["confidence"]           # prob_up mentah — untuk logging/riwayat sinyal
      signal_confidence = result["signal_confidence"]     # keyakinan terhadap arah — untuk keputusan risk
      indicators        = result.get("indicators", {})

      self._save_signal(db, signal, confidence, current_price, indicators)
      print(f"[BotEngine] Sinyal: {signal} (prob_up: {confidence:.2%}, confidence arah: {signal_confidence:.2%})")

      open_count = db.query(Trade).filter(Trade.status == TradeStatus.OPEN).count()

      allowed, reason = self.risk_manager.should_open_trade(
        signal, signal_confidence, open_count, self.capital
      )

      if allowed:
        await self._open_position(db, signal, signal_confidence, current_price)
      else:
        print(f"[BotEngine] Trade dilewati: {reason}")

    finally:
      db.close()

  async def _check_open_positions(self, db: Session, current_price: float):
    open_trades = db.query(Trade).filter(Trade.status == TradeStatus.OPEN).all()
    for trade in open_trades:
      should_close, reason = self.risk_manager.should_close_trade(
        current_price=current_price,
        entry_price=trade.entry_price,
        stop_loss=trade.stop_loss,
        take_profit=trade.take_profit,
        side=trade.action.value,
      )
      if should_close:
        await self._close_position(db, trade, current_price, reason)

  async def _open_position(self, db: Session, signal: str, confidence: float, current_price: float):
    plan = self.risk_manager.build_order_plan(
        signal=signal, confidence=confidence,
        entry_price=current_price, capital=self.capital,
    )

    if plan.quantity <= 0:
      print("[BotEngine] Quantity terlalu kecil, trade dilewati")
      return

    trade = Trade(
      symbol=plan.symbol, action=TradeAction(plan.side),
      status=TradeStatus.OPEN, entry_price=plan.entry_price,
      quantity=plan.quantity, stop_loss=plan.stop_loss,
      take_profit=plan.take_profit, is_paper=self.is_paper,
      opened_at=datetime.now(timezone.utc),
    )
    db.add(trade)
    db.commit()
    db.refresh(trade)

    mode = "📋 PAPER" if self.is_paper else "💰 LIVE"
    print(
      f"[BotEngine] {mode} ORDER OPENED — "
      f"{plan.side} {plan.quantity} {plan.symbol} @ ${plan.entry_price:,.2f} | "
      f"SL: ${plan.stop_loss:,.2f} | TP: ${plan.take_profit:,.2f} | "
      f"Risk: ${plan.risk_amount:.2f}"
    )

    if not self.is_paper:
      await self._send_live_order(plan)

  async def _close_position(self, db: Session, trade: Trade, exit_price: float, reason: str):
    if trade.action == TradeAction.BUY:
      pnl = (exit_price - trade.entry_price) * trade.quantity
    else:
      pnl = (trade.entry_price - exit_price) * trade.quantity

    pnl_pct = pnl / (trade.entry_price * trade.quantity)
    self.capital += pnl

    trade.status     = TradeStatus.CLOSED
    trade.exit_price = exit_price
    trade.pnl        = round(pnl, 4)
    trade.pnl_pct    = round(pnl_pct, 6)
    trade.closed_at  = datetime.now(timezone.utc)
    db.commit()

    emoji = "✅" if pnl > 0 else "❌"
    print(
      f"[BotEngine] {emoji} POSITION CLOSED ({reason.upper()}) — "
      f"PnL: ${pnl:+.2f} ({pnl_pct:+.2%}) | Kapital: ${self.capital:,.2f}"
    )

  async def _send_live_order(self, plan):
    print("[BotEngine] Live order — belum diimplementasi, pastikan paper trading dulu")

  def _save_signal(self, db: Session, signal: str, confidence: float, price: float, indicators: dict):
    db.add(Signal(
      symbol=settings.SYMBOL, signal=SignalType(signal),
      confidence=confidence, price=price,
      rsi=indicators.get("rsi_14"), macd=indicators.get("macd"),
    ))
    db.commit()


bot = BotEngine()