import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from xgboost import XGBClassifier
from sklearn.model_selection import TimeSeriesSplit
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import accuracy_score, classification_report

from backend.ml.features import engineer_features, FEATURE_COLUMNS
from backend.services.data_fetcher import ohlcv_to_dataframe

# Path tempat model disimpan
MODEL_PATH = Path(__file__).parent / "model.pkl"


def train_model(candles: list[dict]) -> dict:
  """
  Train model XGBoost dari data OHLCV.

  Args:
    candles: list candle dict dari fetch_ohlcv atau DB

  Returns:
    dict berisi metrics hasil training
  """
  # 1. Konversi ke DataFrame & feature engineering
  df_raw = ohlcv_to_dataframe(candles)
  df     = engineer_features(df_raw)

  if len(df) < 100:
    raise ValueError(f"Data terlalu sedikit: {len(df)} baris. Minimal 100.")

  X = df[FEATURE_COLUMNS]
  y = df["target"]

  print(f"[Trainer] Total data: {len(df)} baris")
  print(f"[Trainer] Target distribusi: {y.value_counts().to_dict()}")

  # 2. Walk-forward validation — wajib untuk time series
  tscv    = TimeSeriesSplit(n_splits=5)
  metrics = []

  base_model = XGBClassifier(
    n_estimators=300,
    max_depth=4,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    min_child_weight=5,
    gamma=0.1,
    eval_metric="logloss",
    random_state=42,
    verbosity=0,
  )

  for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
    X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
    y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

    base_model.fit(
      X_train, y_train,
      eval_set=[(X_val, y_val)],
      verbose=False,
    )

    preds = base_model.predict(X_val)
    acc   = accuracy_score(y_val, preds)
    metrics.append(acc)
    print(f"[Trainer] Fold {fold + 1}/5 — Accuracy: {acc:.3f}")

  mean_acc = np.mean(metrics)
  print(f"[Trainer] Mean accuracy: {mean_acc:.3f}")

  # 3. Train final model pada semua data
  # Pakai CalibratedClassifierCV agar output probabilitas reliable
  final_model = CalibratedClassifierCV(
    XGBClassifier(
      n_estimators=300,
      max_depth=4,
      learning_rate=0.05,
      subsample=0.8,
      colsample_bytree=0.8,
      min_child_weight=5,
      gamma=0.1,
      eval_metric="logloss",
      random_state=42,
      verbosity=0,
    ),
    method="isotonic",
    cv=3,
  )
  final_model.fit(X, y)

  # 4. Simpan model ke disk
  joblib.dump(final_model, MODEL_PATH)
  print(f"[Trainer] Model disimpan ke: {MODEL_PATH}")

  # 5. Feature importance (dari base estimator pertama)
  try:
    importances = base_model.feature_importances_
    feat_imp = dict(zip(FEATURE_COLUMNS, importances.tolist()))
    top_features = sorted(feat_imp.items(), key=lambda x: x[1], reverse=True)[:5]
  except Exception:
    top_features = []

  return {
    "status":        "success",
    "total_samples": len(df),
    "mean_accuracy": round(mean_acc, 4),
    "fold_scores":   [round(m, 4) for m in metrics],
    "top_features":  top_features,
    "model_path":    str(MODEL_PATH),
  }


def load_model():
  """Load model dari disk. Return None kalau belum ada."""
  if not MODEL_PATH.exists():
      return None
  return joblib.load(MODEL_PATH)


def model_exists() -> bool:
  return MODEL_PATH.exists()