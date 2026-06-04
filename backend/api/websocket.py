from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from datetime import datetime
import asyncio
import json

from backend.services.exchange import fetch_ticker
from backend.services.bot_engine import bot
from backend.config import get_settings

settings = get_settings()
router   = APIRouter()

class ConnectionManager:
  """Manage multiple WebSocket connections."""
  
  def __init__(self):
    self.active: list[WebSocket] = []

  async def connect(self, ws: WebSocket):
    await ws.accept()
    self.active.append(ws)
    print(f"[WS] Client connected — total: {len(self.active)}")

  def disconnect(self, ws: WebSocket):
    if ws in self.active:
      self.active.remove(ws)
    print(f"[WS] Client disconnected — total: {len(self.active)}")

  async def broadcast(self, data: dict):
    disconnected = []
    for ws in self.active:
      try:
        await ws.send_text(json.dumps(data, default=str))
      except Exception:
        disconnected.append(ws)
    for ws in disconnected:
      self.disconnect(ws)

manager = ConnectionManager()

@router.websocket("/ws/live")
async def live_feed(ws: WebSocket):
  """
  Stream data live ke frontend setiap 5 detik:
  - Harga terkini dari Binance
  - Status bot (running/stopped, kapital)
  - Sinyal terakhir
  """
  await manager.connect(ws)
  try:
    while True:
      try:
        # Fetch harga real dari Binance
        ticker     = fetch_ticker(settings.SYMBOL)
        bot_status = bot.get_status()

        payload = {
          "type":      "live_update",
          "symbol":    ticker["symbol"],
          "price":     ticker["last"],
          "change_pct": ticker["change_pct"],
          "high":      ticker["high"],
          "low":       ticker["low"],
          "volume":    ticker["volume"],
          "bot": {
            "running":  bot_status["running"],
            "is_paper": bot_status["is_paper"],
            "capital":  bot_status["capital"],
          },
          "timestamp": datetime.utcnow().isoformat(),
        }

        await ws.send_text(json.dumps(payload, default=str))

      except Exception as e:
        # Kalau fetch gagal, kirim error tapi jangan putus koneksi
        await ws.send_text(json.dumps({
          "type":  "error",
          "message": str(e),
          "timestamp": datetime.utcnow().isoformat(),
        }))

        await asyncio.sleep(5)

  except WebSocketDisconnect:
    manager.disconnect(ws)
  except Exception as e:
    manager.disconnect(ws)
    print(f"[WS] Error: {e}")