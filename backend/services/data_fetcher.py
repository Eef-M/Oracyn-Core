import time
import pandas as pd
from datetime import datetime, timezone
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
  Ambil OHLCV dari exchange, simpan ke DB, return sebagai list dict.
  Untuk limit > 1000: otomatis pakai pagination (fetch bertahap).
  """
  symbol    = symbol    or settings.SYMBOL
  timeframe = timeframe or settings.TIMEFRAME

  # Binance max 1000 candle per request — pakai pagination kalau lebih
  if limit <= 1000:
      candles = fetch_ohlcv_sync(symbol, timeframe, limit)
  else:
      candles = _fetch_ohlcv_paginated(symbol, timeframe, limit)

  _save_candles_to_db(db, candles, symbol, timeframe)
  return candles


def _fetch_ohlcv_paginated(
  symbol: str,
  timeframe: str,
  total_limit: int,
) -> list[dict]:
  """
  Fetch data OHLCV dalam beberapa batch menggunakan since parameter.
  Binance max 1000 candle per request, jadi kita fetch bertahap dari
  yang paling lama ke yang terbaru.
  """
  import ccxt
  from backend.services.exchange import get_exchange

  exchange       = get_exchange()
  batch_size     = 1000
  all_candles    = []
  fetched_so_far = 0

  # Hitung waktu mulai berdasarkan total candle yang diinginkan
  # timeframe_ms = durasi satu candle dalam milliseconds
  tf_ms_map = {
    "1m":  60_000,
    "5m":  300_000,
    "15m": 900_000,
    "1h":  3_600_000,
    "4h":  14_400_000,
    "1d":  86_400_000,
  }
  tf_ms = tf_ms_map.get(timeframe, 3_600_000)

  # Mulai dari waktu (total_limit candle yang lalu)
  since = int(datetime.now(timezone.utc).timestamp() * 1000) - (total_limit * tf_ms)

  print(f"[DataFetcher] Mulai fetch {total_limit} candle {symbol} {timeframe} via pagination...")

  while fetched_so_far < total_limit:
    remaining  = total_limit - fetched_so_far
    batch      = min(batch_size, remaining)

    try:
      raw = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=batch)
    except Exception as e:
      print(f"[DataFetcher] Error saat fetch batch: {e}")
      break

    if not raw:
      break

    parsed = [
      {
        "timestamp": exchange.iso8601(c[0]),
        "open":  c[1], "high":  c[2],
        "low":   c[3], "close": c[4], "volume": c[5],
      }
      for c in raw
    ]
    all_candles.extend(parsed)
    fetched_so_far += len(raw)

    # Update since ke timestamp candle terakhir + 1ms
    since = raw[-1][0] + 1

    print(f"[DataFetcher] Fetched {fetched_so_far}/{total_limit} candle...")

    # Rate limit — hindari hit limit Binance
    if fetched_so_far < total_limit:
      time.sleep(0.3)

  print(f"[DataFetcher] Total fetched: {len(all_candles)} candle")
  return all_candles


def _save_candles_to_db(
  db: Session,
  candles: list[dict],
  symbol: str,
  timeframe: str,
) -> int:
  """Simpan candles ke DB, skip duplikat. Return jumlah yang disimpan."""
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
  print(f"[DataFetcher] {symbol} {timeframe}: {saved} candle baru disimpan ke DB")
  return saved


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
      "open":  row.open,  "high": row.high,
      "low":   row.low,   "close": row.close,
      "volume": row.volume,
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
    "low":  float, "close": float, "volume": float,
  })
  return df