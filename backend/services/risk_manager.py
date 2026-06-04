from dataclasses import dataclass
from backend.config import get_settings

settings = get_settings()

@dataclass
class OrderPlan:
  """Rencana order yang sudah dihitung risk-nya."""
  symbol:       str
  side:         str    # "BUY" atau "SELL"
  entry_price:  float
  quantity:     float
  stop_loss:    float
  take_profit:  float
  risk_amount:  float  # nominal uang yang di-risk (USDT)
  kelly_pct:    float  # % bankroll dari Kelly Criterion


class RiskManager:
  """
  Mengelola semua keputusan risk sebelum order dikirim.

  Tanggung jawab:
  - Hitung position size yang aman
  - Hitung stop-loss & take-profit
  - Validasi apakah trade boleh dibuka
  - Kelly Criterion untuk bet sizing
  """

  def __init__(self):
    self.max_risk_per_trade = settings.MAX_RISK_PER_TRADE  # default 2%
    self.stop_loss_pct      = settings.STOP_LOSS_PCT        # default 3%
    self.take_profit_ratio  = 2.0    # risk:reward = 1:2
    self.max_open_trades    = 3      # maksimal 3 posisi terbuka sekaligus
    self.min_confidence     = 0.55   # minimum confidence model untuk trade

  # ── Position sizing ────────────────────────────────────────────────────

  def calculate_position_size(
    self,
    capital: float,
    entry_price: float,
    stop_loss_price: float,
  ) -> float:
    """
    Hitung quantity yang aman berdasarkan fixed fractional risk.

    Formula:
      risk_amount  = capital * max_risk_per_trade
      risk_per_unit = entry_price - stop_loss_price
      quantity     = risk_amount / risk_per_unit

    Contoh:
      capital = 10.000 USDT, risk 2% = 200 USDT
      entry = 70.000, stop_loss = 67.900 (3% di bawah)
      risk_per_unit = 2.100
      quantity = 200 / 2.100 = 0.0952 BTC
    """
    risk_amount   = capital * self.max_risk_per_trade
    risk_per_unit = abs(entry_price - stop_loss_price)

    if risk_per_unit == 0:
      return 0.0

    quantity = risk_amount / risk_per_unit

    # Pastikan tidak melebihi 20% kapital dalam satu trade
    max_quantity = (capital * 0.20) / entry_price
    quantity = min(quantity, max_quantity)

    # Round ke 6 desimal (standar crypto)
    return round(quantity, 6)

  def calculate_stop_loss(self, entry_price: float, side: str) -> float:
    """Hitung harga stop-loss berdasarkan persentase dari config."""
    if side == "BUY":
      return round(entry_price * (1 - self.stop_loss_pct), 2)
    else:
      return round(entry_price * (1 + self.stop_loss_pct), 2)

  def calculate_take_profit(self, entry_price: float, stop_loss: float, side: str) -> float:
    """Hitung take-profit dengan risk:reward ratio."""
    risk = abs(entry_price - stop_loss)
    reward = risk * self.take_profit_ratio
    if side == "BUY":
      return round(entry_price + reward, 2)
    else:
      return round(entry_price - reward, 2)

  def kelly_fraction(self, confidence: float) -> float:
    """
    Hitung Kelly Criterion fraction dari confidence model.

    Kelly = (p * b - q) / b
    p = probabilitas menang (confidence model)
    q = 1 - p
    b = odds (risk:reward ratio)

    Pakai fractional Kelly (25%) untuk safety.
    """
    p = confidence
    q = 1 - p
    b = self.take_profit_ratio

    kelly = (p * b - q) / b
    kelly = max(0.0, kelly)          # tidak boleh negatif
    fractional_kelly = kelly * 0.25  # pakai 25% dari full Kelly

    # Cap maksimal 5% dari kapital
    return round(min(fractional_kelly, 0.05), 4)

  # ── Validasi ────────────────────────────────────────────────────────────

  def should_open_trade(
    self,
    signal: str,
    confidence: float,
    open_trades_count: int,
    capital: float,
  ) -> tuple[bool, str]:
    """
    Validasi apakah trade boleh dibuka.

    Returns:
        (boleh_trade, alasan_penolakan)
    """
    if signal == "HOLD":
      return False, "Signal HOLD — no action"

    if confidence < self.min_confidence:
      return False, f"Confidence {confidence:.2%} is below the minimum {self.min_confidence:.2%}"

    if open_trades_count >= self.max_open_trades:
      return False, f"There are already {open_trades_count} open positions (max {self.max_open_trades})"

    if capital < 10:
      return False, f"Capital too low: {capital:.2f} USDT"

    return True, "OK"

  def should_close_trade(
    self,
    current_price: float,
    entry_price: float,
    stop_loss: float,
    take_profit: float,
    side: str,
  ) -> tuple[bool, str]:
    """
    Cek apakah posisi yang sudah terbuka harus ditutup.

    Returns:
      (harus_tutup, alasan)
    """
    if side == "BUY":
      if current_price <= stop_loss:
        return True, "stop_loss"
      if current_price >= take_profit:
        return True, "take_profit"
    elif side == "SELL":
      if current_price >= stop_loss:
        return True, "stop_loss"
      if current_price <= take_profit:
        return True, "take_profit"

    return False, "hold"

  # ── Order plan ──────────────────────────────────────────────────────────

  def build_order_plan(
    self,
    signal: str,
    confidence: float,
    entry_price: float,
    capital: float,
  ) -> OrderPlan:
    """
    Buat rencana order lengkap dengan semua parameter risk.
    """
    side        = "BUY" if signal == "BUY" else "SELL"
    stop_loss   = self.calculate_stop_loss(entry_price, side)
    take_profit = self.calculate_take_profit(entry_price, stop_loss, side)
    quantity    = self.calculate_position_size(capital, entry_price, stop_loss)
    kelly_pct   = self.kelly_fraction(confidence)
    risk_amount = quantity * abs(entry_price - stop_loss)

    return OrderPlan(
      symbol      = settings.SYMBOL,
      side        = side,
      entry_price = entry_price,
      quantity    = quantity,
      stop_loss   = stop_loss,
      take_profit = take_profit,
      risk_amount = round(risk_amount, 2),
      kelly_pct   = kelly_pct,
    )