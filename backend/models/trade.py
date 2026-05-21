from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Enum
from sqlalchemy.sql import func
import enum
from backend.database import Base


class TradeAction(str, enum.Enum):
  BUY = "BUY"
  SELL = "SELL"


class TradeStatus(str, enum.Enum):
  OPEN = "OPEN"
  CLOSED = "CLOSED"


class Trade(Base):
  __tablename__ = "trades"

  id            = Column(Integer, primary_key=True, index=True)
  symbol        = Column(String, nullable=False, index=True)
  action        = Column(Enum(TradeAction), nullable=False)
  status        = Column(Enum(TradeStatus), default=TradeStatus.OPEN)
  entry_price   = Column(Float, nullable=False)
  exit_price    = Column(Float, nullable=True)
  quantity      = Column(Float, nullable=False)
  pnl           = Column(Float, nullable=True)          # realized PnL
  pnl_pct       = Column(Float, nullable=True)          # PnL dalam %
  stop_loss     = Column(Float, nullable=True)
  take_profit   = Column(Float, nullable=True)
  is_paper      = Column(Boolean, default=True)         # paper trade atau live
  opened_at     = Column(DateTime(timezone=True), server_default=func.now())
  closed_at     = Column(DateTime(timezone=True), nullable=True)