from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from backend.database import SessionLocal
from backend.services.data_fetcher import fetch_and_store_ohlcv
from backend.ml.trainer import train_model
from backend.config import get_settings

settings = get_settings()

scheduler = AsyncIOScheduler(timezone="UTC")

# ── Job 1: Fetch OHLCV terbaru setiap 5 menit ─────────────
async def job_fetch_ohlcv():
  """Simpan candle terbaru ke database agar data selalu fresh."""
  db = SessionLocal()
  try:
    candles = fetch_and_store_ohlcv(db, limit=10)  # hanya ambil 10 candle terbaru
    print(f"[Scheduler] OHLCV updated — {len(candles)} candle")
  except Exception as e:
    print(f"[Scheduler] Error fetch OHLCV: {e}")
  finally:
    db.close()

# ── Job 2: Retrain model setiap hari pukul 00:00 UTC ──────
async def job_retrain_model():
  """
  Retrain model dengan data terbaru setiap hari.
  Ini penting agar model tidak drift seiring perubahan pasar.
  """
  db = SessionLocal()
  try:
    print("[Scheduler] Starting to retrain daily models...")
    candles = fetch_and_store_ohlcv(db, limit=1000)
    result  = train_model(candles)
    print(
      f"[Scheduler] Retrain completed — "
      f"accuracy: {result['mean_accuracy']:.4f}, "
      f"samples: {result['total_samples']}"
    )
  except Exception as e:
    print(f"[Scheduler] Error retrain: {e}")
  finally:
    db.close()


def start_scheduler():
  """Daftarkan semua job dan jalankan scheduler."""
  # Fetch OHLCV setiap 5 menit
  scheduler.add_job(
    job_fetch_ohlcv,
    trigger=IntervalTrigger(minutes=5),
    id="fetch_ohlcv",
    name="Fetch the latest OHLCV",
    replace_existing=True,
  )

  # Retrain model setiap hari pukul 00:05 UTC (setelah fetch selesai)
  scheduler.add_job(
    job_retrain_model,
    trigger=CronTrigger(hour=0, minute=5, timezone="UTC"),
    id="retrain_model",
    name="Daily model retrain",
    replace_existing=True,
  )

  scheduler.start()
  print("[Scheduler] ✅ Scheduler is running")
  print("[Scheduler]   • Fetch OHLCV: every 5 minutes")
  print("[Scheduler]   • Retrain model: every day at 00:05 UTC")


def stop_scheduler():
  if scheduler.running:
    scheduler.shutdown()
    print("[Scheduler] Scheduler stopped")