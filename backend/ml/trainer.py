import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from xgboost import XGBClassifier
from sklearn.model_selection import TimeSeriesSplit
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import accuracy_score, precision_score, recall_score

from backend.ml.features import engineer_features, FEATURE_COLUMNS
from backend.services.data_fetcher import ohlcv_to_dataframe

MODEL_PATH = Path(__file__).parent / "model.pkl"


def train_model(
  candles: list[dict],
  horizon: int = 6,
  threshold_pct: float = 0.005,
) -> dict:
  """
  Train model XGBoost dari data OHLCV.

  Args:
    candles:       list candle dict dari fetch_ohlcv atau DB
    horizon:       berapa candle ke depan target diukur
    threshold_pct: ambang minimum gerakan harga dianggap sinyal (bukan noise).
                   Default 0.005 divalidasi via confidence_bucket_analysis.py —
                   satu-satunya kombinasi dengan edge SELL yang signifikan
                   secara konsisten di semua level confidence cutoff.

  Returns:
    dict berisi metrics hasil training
  """
  df_raw = ohlcv_to_dataframe(candles)
  df     = engineer_features(df_raw, horizon=horizon, threshold_pct=threshold_pct)

  # Minimal data dinaikkan — dengan fitur lebih banyak (28 fitur),
  # butuh lebih banyak sample agar tidak overfit
  if len(df) < 300:
    raise ValueError(
      f"Data terlalu sedikit setelah exclude zona netral: {len(df)} baris. "
      f"Minimal 300. Coba naikkan parameter limit saat fetch data, "
      f"atau kecilkan threshold_pct."
    )

  X = df[FEATURE_COLUMNS]
  y = df["target"].astype(int)

  print(f"[Trainer] Total data (setelah exclude zona netral): {len(df)} baris")
  print(f"[Trainer] Target distribusi: {y.value_counts().to_dict()}")

  # Cek class imbalance — kalau salah satu kelas terlalu dominan,
  # model bisa "curang" dengan selalu prediksi kelas mayoritas
  class_balance = y.value_counts(normalize=True)
  if class_balance.min() < 0.35:
    print(
      f"[Trainer] ⚠ Peringatan: class imbalance terdeteksi "
      f"({class_balance.to_dict()}). Pertimbangkan ubah threshold_pct."
    )

  tscv    = TimeSeriesSplit(n_splits=5)
  metrics = []
  precisions = []
  recalls    = []

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
    acc    = accuracy_score(y_val, preds)
    # Precision & recall lebih informatif dari accuracy saja —
    # accuracy bisa menipu kalau class imbalance
    prec   = precision_score(y_val, preds, zero_division=0)
    rec    = recall_score(y_val, preds, zero_division=0)

    metrics.append(acc)
    precisions.append(prec)
    recalls.append(rec)
    print(
      f"[Trainer] Fold {fold + 1}/5 — "
      f"Accuracy: {acc:.3f} | Precision: {prec:.3f} | Recall: {rec:.3f}"
    )

  mean_acc  = np.mean(metrics)
  mean_prec = np.mean(precisions)
  mean_rec  = np.mean(recalls)
  print(f"[Trainer] Mean accuracy: {mean_acc:.3f} | precision: {mean_prec:.3f} | recall: {mean_rec:.3f}")

  # Train final model pada semua data dengan kalibrasi probabilitas
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

  joblib.dump(final_model, MODEL_PATH)
  print(f"[Trainer] Model disimpan ke: {MODEL_PATH}")

  try:
    importances = base_model.feature_importances_
    feat_imp = dict(zip(FEATURE_COLUMNS, importances.tolist()))
    top_features = sorted(feat_imp.items(), key=lambda x: x[1], reverse=True)[:8]
  except Exception:
    top_features = []

  return {
    "status":          "success",
    "total_samples":   len(df),
    "mean_accuracy":   round(mean_acc, 4),
    "mean_precision":  round(mean_prec, 4),
    "mean_recall":     round(mean_rec, 4),
    "fold_scores":     [round(m, 4) for m in metrics],
    "class_balance":   class_balance.to_dict(),
    "top_features":    top_features,
    "horizon":         horizon,
    "threshold_pct":   threshold_pct,
    "model_path":      str(MODEL_PATH),
  }


def load_model():
  if not MODEL_PATH.exists():
    return None
  return joblib.load(MODEL_PATH)


def model_exists() -> bool:
  return MODEL_PATH.exists()