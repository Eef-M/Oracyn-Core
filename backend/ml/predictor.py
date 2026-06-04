import pandas as pd
from datetime import datetime

from backend.ml.features import engineer_features, FEATURE_COLUMNS
from backend.ml.trainer import load_model, model_exists
from backend.services.data_fetcher import ohlcv_to_dataframe
from backend.config import get_settings

settings = get_settings()

# Threshold probabilitas untuk keputusan sinyal
BUY_THRESHOLD  = 0.62   # probabilitas naik > 62% → BUY
SELL_THRESHOLD = 0.40   # probabilitas naik < 40% → SELL
                         # antara 40-62% → HOLD


def predict_signal(candles: list[dict]) -> dict:
  """
  Generate sinyal trading dari data OHLCV terbaru.

  Args:
    candles: list candle OHLCV (minimal 60 candle untuk indikator stabil)

  Returns:
    dict berisi signal, confidence, price, dan detail indikator
  """
  if not model_exists():
    return {
      "signal":     "HOLD",
      "confidence": 0.0,
      "reason":     "The model hasn't been trained yet. POST /api/ml/train first.",
      "price":      candles[-1]["close"] if candles else 0,
      "timestamp":  datetime.utcnow().isoformat(),
    }

  model = load_model()

  # Feature engineering
  df_raw = ohlcv_to_dataframe(candles)
  df     = engineer_features(df_raw)

  if df.empty:
    return {
      "signal":     "HOLD",
      "confidence": 0.0,
      "reason":     "Not enough data to generate features.",
      "price":      candles[-1]["close"],
      "timestamp":  datetime.utcnow().isoformat(),
    }

  # Ambil baris terakhir (kondisi pasar terkini)
  latest      = df[FEATURE_COLUMNS].iloc[[-1]]
  latest_row  = df.iloc[-1]
  price       = float(df_raw["close"].iloc[-1])

  # Prediksi probabilitas
  proba  = model.predict_proba(latest)[0]
  prob_up = float(proba[1])   # probabilitas harga naik

  # Tentukan sinyal
  if prob_up >= BUY_THRESHOLD:
    signal = "BUY"
  elif prob_up <= SELL_THRESHOLD:
    signal = "SELL"
  else:
    signal = "HOLD"

  return {
    "signal":     signal,
    "confidence": round(prob_up, 4),
    "price":      round(price, 2),
    "symbol":     settings.SYMBOL,
    "timestamp":  datetime.utcnow().isoformat(),
    "indicators": {
      "rsi_14":      round(float(latest_row["rsi_14"]), 2),
      "macd":        round(float(latest_row["macd"]), 4),
      "macd_signal": round(float(latest_row["macd_signal"]), 4),
      "bb_pct":      round(float(latest_row["bb_pct"]), 4),
      "volume_ratio": round(float(latest_row["volume_ratio"]), 2),
      "atr_pct":     round(float(latest_row["atr_pct"]), 4),
    },
    "thresholds": {
      "buy":  BUY_THRESHOLD,
      "sell": SELL_THRESHOLD,
    },
  }