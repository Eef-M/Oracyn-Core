from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from datetime import datetime
import asyncio
import json
import random  # nanti diganti dengan data real dari exchange

router = APIRouter()

class ConnectionManager:
  """Manage multiple WebSocket connections."""
 
  def __init__(self):
      self.active: list[WebSocket] = []

  async def connect(self, ws: WebSocket):
      await ws.accept()
      self.active.append(ws)

  def disconnect(self, ws: WebSocket):
      if ws in self.active:
          self.active.remove(ws)

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
  Stream data live ke frontend setiap 3 detik.
  Saat ini mengirim mock data — nanti diganti data real dari exchange.
  """
  await manager.connect(ws)
  try:
      base_price = 65000.0
      while True:
          # Mock price update — ganti dengan fetch dari ccxt
          price = base_price + random.uniform(-200, 200)
          signal = random.choice(["BUY", "SELL", "HOLD"])
          confidence = round(random.uniform(0.5, 0.95), 3)

          payload = {
              "symbol": "BTC/USDT",
              "price": round(price, 2),
              "signal": signal,
              "confidence": confidence,
              "timestamp": datetime.utcnow().isoformat(),
          }
          await ws.send_text(json.dumps(payload))
          await asyncio.sleep(3)
 
  except WebSocketDisconnect:
      manager.disconnect(ws)
  except Exception as e:
      manager.disconnect(ws)
      print(f"[WS] Error: {e}")