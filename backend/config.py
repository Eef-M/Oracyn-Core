from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
  # App
  APP_NAME: str = "Oracyn Core"
  DEBUG: bool = False

  # Exchange
  BINANCE_API_KEY: str = ""
  BINANCE_SECRET: str = ""
  EXCHANGE: str = "binance"
  SYMBOL: str = "BTC/USDT"
  TIMEFRAME: str = "1h"

  # Database
  DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/oracyn_core_db"

  # Redis
  REDIS_URL: str = "redis://localhost:6379"

  # Bot
  BOT_ENAVLED: bool = False
  INITIAL_CAPITAL: float = 10000.0
  MAX_RISK_PER_TRADE: float = 0.02
  STOP_LOSS_PCT: float = 0.03

  class config:
    env_file = ".env"
    env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
  return Settings()