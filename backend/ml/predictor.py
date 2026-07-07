import pandas as pd
from datetime import datetime

from backend.ml.features import engineer_features, FEATURE_COLUMNS
from backend.ml.trainer import load_model, model_exists
from backend.services.data_fetcher import ohlcv_to_dataframe
from backend.config import get_settings

settings = get_settings()

# ── Threshold probabilitas untuk keputusan sinyal ──────────────────────
ENABLE_BUY_SIGNAL = False

BUY_THRESHOLD  = 0.62
SELL_THRESHOLD = 0.40


def predict_signal(candles: list[dict]) -> dict:
  """
  Generate sinyal trading dari data OHLCV terbaru.

  Args:
    candles: list candle OHLCV (minimal ~210 candle agar EMA200
              dan indikator lain punya cukup data historis)

  Returns:
    dict berisi signal, confidence, price, dan detail indikator
  """
  if not model_exists():
    return {
      "signal":     "HOLD",
      "confidence": 0.0,
      "reason":     "Model belum ditraining. Jalankan POST /api/ml/train dulu.",
      "price":      candles[-1]["close"] if candles else 0,
      "timestamp":  datetime.utcnow().isoformat(),
    }

  model = load_model()

  df_raw = ohlcv_to_dataframe(candles)

  # engineer_features sekarang butuh data lebih banyak karena EMA200
  # — kalau data tidak cukup, baris terakhir akan ke-drop semua
  if len(df_raw) < 210:
    return {
      "signal":     "HOLD",
      "confidence": 0.0,
      "reason":     f"Data tidak cukup ({len(df_raw)} candle). Minimal 210 untuk EMA200.",
      "price":      float(df_raw["close"].iloc[-1]) if len(df_raw) > 0 else 0,
      "timestamp":  datetime.utcnow().isoformat(),
    }

  # Mode inference: compute_target=False — TIDAK menghitung target/future_return,
  # sehingga candle paling baru tidak ikut terbuang oleh dropna (lihat fix di
  # features.py). Ini memastikan sinyal dihasilkan dari candle yang benar-benar
  # terkini, bukan tertinggal `horizon` candle di belakang.
  df = engineer_features(df_raw, compute_target=False)

  if df.empty:
    return {
      "signal":     "HOLD",
      "confidence": 0.0,
      "reason":     "Data tidak cukup untuk generate fitur.",
      "price":      float(df_raw["close"].iloc[-1]),
      "timestamp":  datetime.utcnow().isoformat(),
    }

  latest      = df[FEATURE_COLUMNS].iloc[[-1]]
  latest_row  = df.iloc[-1]
  price       = float(df_raw["close"].iloc[-1])

  proba   = model.predict_proba(latest)[0]
  prob_up = float(proba[1])

  would_buy      = prob_up >= BUY_THRESHOLD
  buy_suppressed = would_buy and not ENABLE_BUY_SIGNAL

  if would_buy and ENABLE_BUY_SIGNAL:
    signal = "BUY"
  elif prob_up <= SELL_THRESHOLD:
    signal = "SELL"
  else:
    signal = "HOLD"

  # ── signal_confidence: keyakinan terhadap ARAH sinyal ──────────────────
  if signal == "SELL":
    signal_confidence = round(1 - prob_up, 4)
  else:
    signal_confidence = round(prob_up, 4)

  return {
    "signal":            signal,
    "confidence":        round(prob_up, 4),        # prob_up mentah — untuk logging/analisis
    "signal_confidence": signal_confidence,          # keyakinan terhadap arah — untuk risk_manager
    "price":             round(price, 2),
    "symbol":            settings.SYMBOL,
    "timestamp":         datetime.utcnow().isoformat(),
    "buy_suppressed":    buy_suppressed,  # True = model mau BUY tapi ditahan (belum ada edge terbukti)
    "indicators": {
      "rsi_14":       round(float(latest_row["rsi_14"]), 2),
      "macd":         round(float(latest_row["macd"]), 4),
      "macd_signal":  round(float(latest_row["macd_signal"]), 4),
      "bb_pct":       round(float(latest_row["bb_pct"]), 4),
      "volume_ratio": round(float(latest_row["volume_ratio"]), 2),
      "atr_pct":      round(float(latest_row["atr_pct"]), 4),
      "adx":          round(float(latest_row["adx"]), 2),
      "above_ema_200": bool(latest_row["above_ema_200"]),
    },
    "thresholds": {
      "buy":            BUY_THRESHOLD,
      "sell":           SELL_THRESHOLD,
      "buy_enabled":    ENABLE_BUY_SIGNAL,
    },
  }