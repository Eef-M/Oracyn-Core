from sqlalchemy import Column, Integer, String, Float, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from backend.database import Base


class OHLCV(Base):
  __tablename__ = "ohlcv"

  id        = Column(Integer, primary_key=True, index=True)
  symbol    = Column(String, nullable=False, index=True)
  timeframe = Column(String, nullable=False)
  timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
  open      = Column(Float, nullable=False)
  high      = Column(Float, nullable=False)
  low       = Column(Float, nullable=False)
  close     = Column(Float, nullable=False)
  volume    = Column(Float, nullable=False)
  created_at = Column(DateTime(timezone=True), server_default=func.now())

  # Pastikan tidak ada duplikat candle untuk symbol + timeframe + timestamp
  __table_args__ = (
    UniqueConstraint("symbol", "timeframe", "timestamp", name="uq_ohlcv_symbol_tf_ts"),
  )