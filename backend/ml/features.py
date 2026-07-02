import pandas as pd
import pandas_ta as ta
import numpy as np


def engineer_features(
  df: pd.DataFrame,
  horizon: int = 6,
  threshold_pct: float = 0.004,
) -> pd.DataFrame:
  """
  Hitung semua fitur teknikal dari data OHLCV mentah.

  Args:
      df:            DataFrame dengan kolom timestamp, open, high, low, close, volume
      horizon:       berapa candle ke depan target diukur (default 6 candle = 6 jam di 1h)
      threshold_pct: ambang minimum gerakan harga untuk dianggap sinyal (bukan noise)

  Output: DataFrame dengan tambahan kolom fitur + kolom 'target'
  """
  df = df.copy()

  # ── Trend indicators ──────────────────────────────────
  df["ema_9"]  = ta.ema(df["close"], length=9)
  df["ema_21"] = ta.ema(df["close"], length=21)
  df["ema_50"] = ta.ema(df["close"], length=50)
  df["ema_200"] = ta.ema(df["close"], length=200)

  df["ema_9_21_cross"]  = (df["ema_9"] > df["ema_21"]).astype(int)
  df["ema_21_50_cross"] = (df["ema_21"] > df["ema_50"]).astype(int)
  # Fitur baru — trend jangka panjang sebagai filter konteks
  df["above_ema_200"]   = (df["close"] > df["ema_200"]).astype(int)
  # Jarak relatif harga terhadap EMA — seberapa "jauh" dari rata-rata
  df["dist_ema_21_pct"] = (df["close"] - df["ema_21"]) / df["ema_21"]
  df["dist_ema_50_pct"] = (df["close"] - df["ema_50"]) / df["ema_50"]

  # ── Momentum indicators ───────────────────────────────
  df["rsi_14"] = ta.rsi(df["close"], length=14)
  df["rsi_7"]  = ta.rsi(df["close"], length=7)
  # Fitur baru — perubahan RSI, menangkap momentum dari momentum
  df["rsi_slope"] = df["rsi_14"].diff(3)

  macd = ta.macd(df["close"], fast=12, slow=26, signal=9)
  macd_col   = [c for c in macd.columns if c.startswith("MACD_")][0]
  signal_col = [c for c in macd.columns if c.startswith("MACDs_")][0]
  hist_col   = [c for c in macd.columns if c.startswith("MACDh_")][0]
  df["macd"]        = macd[macd_col]
  df["macd_signal"] = macd[signal_col]
  df["macd_hist"]   = macd[hist_col]
  df["macd_cross"]  = (df["macd"] > df["macd_signal"]).astype(int)
  # Fitur baru — apakah histogram MACD sedang naik (momentum menguat)
  df["macd_hist_rising"] = (df["macd_hist"].diff() > 0).astype(int)

  # ADX — kekuatan trend (bukan arah). Penting untuk filter sinyal palsu
  # saat market sideways/choppy
  adx = ta.adx(df["high"], df["low"], df["close"], length=14)
  adx_col = [c for c in adx.columns if c.startswith("ADX_")][0]
  df["adx"] = adx[adx_col]

  # ── Volatility indicators ──────────────────────────────
  bb = ta.bbands(df["close"], length=20, std=2)
  bb_upper_col  = [c for c in bb.columns if c.startswith("BBU")][0]
  bb_middle_col = [c for c in bb.columns if c.startswith("BBM")][0]
  bb_lower_col  = [c for c in bb.columns if c.startswith("BBL")][0]
  df["bb_upper"]  = bb[bb_upper_col]
  df["bb_middle"] = bb[bb_middle_col]
  df["bb_lower"]  = bb[bb_lower_col]
  df["bb_width"]  = (df["bb_upper"] - df["bb_lower"]) / df["bb_middle"]
  df["bb_pct"]    = (df["close"] - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"])

  atr = ta.atr(df["high"], df["low"], df["close"], length=14)
  df["atr"] = atr
  df["atr_pct"] = df["atr"] / df["close"]
  # Fitur baru — apakah volatilitas sedang naik (regime berubah)
  df["atr_pct_change"] = df["atr_pct"].pct_change(5)

  # ── Volume indicators ──────────────────────────────────
  df["volume_ma_20"]  = df["volume"].rolling(20).mean()
  df["volume_ratio"]  = df["volume"] / df["volume_ma_20"]
  df["volume_spike"]  = (df["volume_ratio"] > 2.0).astype(int)

  # ── Price action ───────────────────────────────────────
  df["return_1"]  = df["close"].pct_change(1)
  df["return_3"]  = df["close"].pct_change(3)
  df["return_6"]  = df["close"].pct_change(6)
  df["return_12"] = df["close"].pct_change(12)
  df["return_24"] = df["close"].pct_change(24)

  df["body_size"]  = abs(df["close"] - df["open"]) / df["open"]
  df["upper_wick"] = (df["high"] - df[["open", "close"]].max(axis=1)) / df["open"]
  df["lower_wick"] = (df[["open", "close"]].min(axis=1) - df["low"]) / df["open"]
  df["is_bullish"] = (df["close"] > df["open"]).astype(int)

  # ── Target variable —──────────────────────
  future_return = df["close"].shift(-horizon) / df["close"] - 1

  df["future_return"] = future_return  # disimpan untuk debugging/analisis
  df["target"] = np.select(
      [future_return > threshold_pct, future_return < -threshold_pct],
      [1, 0],
      default=np.nan,  # zona netral — TIDAK dipakai untuk training
  )

  # Hapus baris dengan NaN — termasuk baris di zona netral (sengaja)
  # dan baris akibat rolling window & shift di awal/akhir data
  df = df.dropna(subset=[c for c in df.columns if c != "future_return"])

  return df


# Daftar fitur yang dipakai model — urutan ini penting, harus konsisten
FEATURE_COLUMNS = [
    "ema_9_21_cross", "ema_21_50_cross", "above_ema_200",
    "dist_ema_21_pct", "dist_ema_50_pct",
    "rsi_14", "rsi_7", "rsi_slope",
    "macd", "macd_signal", "macd_hist", "macd_cross", "macd_hist_rising",
    "adx",
    "bb_width", "bb_pct",
    "atr_pct", "atr_pct_change",
    "volume_ratio", "volume_spike",
    "return_1", "return_3", "return_6", "return_12", "return_24",
    "body_size", "upper_wick", "lower_wick", "is_bullish",
]