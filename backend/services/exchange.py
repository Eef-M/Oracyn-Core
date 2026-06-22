import ccxt
import asyncio
from concurrent.futures import ThreadPoolExecutor
from backend.config import get_settings

settings = get_settings()

# Thread pool khusus untuk semua call ccxt (synchronous/blocking)
# Ini mencegah ccxt membekukan event loop FastAPI utama
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ccxt")


def get_exchange():
    """
    Buat instance exchange berdasarkan setting EXCHANGE di .env.
    Support: bybit, binance.
    """
    name = settings.EXCHANGE.lower()

    if name == "bybit":
        return ccxt.bybit({
            "apiKey": settings.BYBIT_API_KEY or None,
            "secret": settings.BYBIT_SECRET or None,
            "enableRateLimit": True,
            "options": {
                "defaultType": "spot",
                "adjustForTimeDifference": True,
            },
        })

    if name == "binance":
        return ccxt.binance({
            "apiKey": settings.BINANCE_API_KEY or None,
            "secret": settings.BINANCE_SECRET or None,
            "enableRateLimit": True,
            "options": {
                "defaultType":            "spot",
                "fetchCurrencies":        False,
                "adjustForTimeDifference": True,
            },
        })

    raise ValueError(f"Exchange '{name}' tidak didukung. Pilih: bybit, binance")

# ── Fungsi synchronous (dipanggil dari thread pool) ─────────

def _fetch_ticker_sync(symbol: str) -> dict:
    exchange = get_exchange()
    ticker   = exchange.fetch_ticker(symbol)
    return {
        "symbol":     ticker["symbol"],
        "last":       ticker["last"],
        "bid":        ticker["bid"],
        "ask":        ticker["ask"],
        "high":       ticker["high"],
        "low":        ticker["low"],
        "volume":     ticker["baseVolume"],
        "change_pct": round(ticker["percentage"] or 0, 2),
        "timestamp":  ticker["datetime"],
    }


def _fetch_ohlcv_sync(symbol: str, timeframe: str, limit: int) -> list[dict]:
    exchange = get_exchange()
    raw = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    return [
        {
            "timestamp": exchange.iso8601(candle[0]),
            "open":      candle[1],
            "high":      candle[2],
            "low":       candle[3],
            "close":     candle[4],
            "volume":    candle[5],
        }
        for candle in raw
    ]


def _fetch_balance_sync() -> dict:
    exchange = get_exchange()
    balance  = exchange.fetch_balance()
    return {
        asset: {
            "free":  info["free"],
            "used":  info["used"],
            "total": info["total"],
        }
        for asset, info in balance["total"].items()
        if balance["total"][asset] > 0
    }


# ── Public API — async wrapper yang jalan di thread pool ───
# Semua fungsi ini AMAN dipanggil dari async def endpoint
# tanpa membekukan event loop FastAPI

async def fetch_ticker(symbol: str = None) -> dict:
    """Ambil harga ticker terkini — non-blocking."""
    symbol = symbol or settings.SYMBOL
    loop   = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, _fetch_ticker_sync, symbol)


async def fetch_ohlcv(
    symbol: str = None,
    timeframe: str = None,
    limit: int = 500,
) -> list[dict]:
    """Ambil data candlestick OHLCV — non-blocking."""
    symbol    = symbol    or settings.SYMBOL
    timeframe = timeframe or settings.TIMEFRAME
    loop      = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, _fetch_ohlcv_sync, symbol, timeframe, limit)


async def fetch_balance() -> dict:
    """Ambil saldo akun — non-blocking."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, _fetch_balance_sync)


# ── Sync versions — untuk kode yang masih sync (training, scheduler) ─
# Dipakai di tempat yang BUKAN async def, misal trainer.py
def fetch_ticker_sync(symbol: str = None) -> dict:
    return _fetch_ticker_sync(symbol or settings.SYMBOL)


def fetch_ohlcv_sync(symbol: str = None, timeframe: str = None, limit: int = 500) -> list[dict]:
    return _fetch_ohlcv_sync(
        symbol or settings.SYMBOL,
        timeframe or settings.TIMEFRAME,
        limit,
    )