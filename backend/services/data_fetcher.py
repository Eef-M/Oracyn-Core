import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session

from backend.services.exchange import fetch_ohlcv_sync
from backend.models.ohlcv import OHLCV
from backend.config import get_settings

settings = get_settings()


def fetch_and_store_ohlcv(
    db: Session,
    symbol: str = None,
    timeframe: str = None,
    limit: int = 500,
) -> list[dict]:
    """
    Ambil OHLCV dari exchange (sync — dipakai dari endpoint sync/training/scheduler),
    simpan ke DB (skip duplikat), return sebagai list dict.
    """
    symbol    = symbol    or settings.SYMBOL
    timeframe = timeframe or settings.TIMEFRAME

    candles = fetch_ohlcv_sync(symbol, timeframe, limit)

    saved = 0
    for c in candles:
        ts = datetime.fromisoformat(c["timestamp"].replace("Z", "+00:00"))
        exists = db.query(OHLCV).filter(
            OHLCV.symbol    == symbol,
            OHLCV.timeframe == timeframe,
            OHLCV.timestamp == ts,
        ).first()
        if not exists:
            db.add(OHLCV(
                symbol=symbol, timeframe=timeframe, timestamp=ts,
                open=c["open"], high=c["high"], low=c["low"],
                close=c["close"], volume=c["volume"],
            ))
            saved += 1

    db.commit()
    print(f"[DataFetcher] {symbol} {timeframe}: {saved} candle baru disimpan")
    return candles


def get_ohlcv_from_db(
    db: Session,
    symbol: str = None,
    timeframe: str = None,
    limit: int = 500,
) -> list[dict]:
    """Ambil OHLCV dari database — cepat, tidak hit exchange."""
    symbol    = symbol    or settings.SYMBOL
    timeframe = timeframe or settings.TIMEFRAME

    rows = (
        db.query(OHLCV)
        .filter(OHLCV.symbol == symbol, OHLCV.timeframe == timeframe)
        .order_by(OHLCV.timestamp.desc())
        .limit(limit)
        .all()
    )
    rows = list(reversed(rows))

    return [
        {
            "timestamp": row.timestamp.isoformat(),
            "open": row.open, "high": row.high,
            "low": row.low, "close": row.close, "volume": row.volume,
        }
        for row in rows
    ]


def ohlcv_to_dataframe(candles: list[dict]) -> pd.DataFrame:
    """Konversi list OHLCV dict ke pandas DataFrame."""
    df = pd.DataFrame(candles)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.set_index("timestamp")
    df = df.astype({
        "open": float, "high": float,
        "low": float, "close": float, "volume": float,
    })
    return df