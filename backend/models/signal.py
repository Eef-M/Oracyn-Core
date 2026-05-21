from sqlalchemy import Column, Integer, String, Float, DateTime, Enum
from sqlalchemy.sql import func
import enum
from backend.database import Base


class SignalType(str, enum.Enum):
  BUY = "BUY"
  SELL = "SELL"
  HOLD = "HOLD"


class Signal(Base):
  __tablename__ = "signals"

  id           = Column(Integer, primary_key=True, index=True)
  symbol       = Column(String, nullable=False, index=True)
  signal       = Column(Enum(SignalType), nullable=False)
  confidence   = Column(Float, nullable=False)    # probabilitas dari model (0-1)
  price        = Column(Float, nullable=False)    # harga saat sinyal dibuat
  rsi          = Column(Float, nullable=True)
  macd         = Column(Float, nullable=True)
  created_at   = Column(DateTime(timezone=True), server_default=func.now())