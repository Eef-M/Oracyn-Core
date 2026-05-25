from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
  # App
  APP_NAME: str = "Oracyn Core"
  DEBUG: bool = False

  # Exchange
  BINANCE_API_KEY: str
  BINANCE_SECRET: str
  EXCHANGE: str
  SYMBOL: str
  TIMEFRAME: str

  # Database
  DATABASE_URL: str 

  # Redis
  REDIS_URL: str

  # Bot
  BOT_ENABLED: bool
  INITIAL_CAPITAL: float
  MAX_RISK_PER_TRADE: float
  STOP_LOSS_PCT: float

  model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

@lru_cache()
def get_settings() -> Settings:
  return Settings()