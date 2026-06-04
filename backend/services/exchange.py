import ccxt
from backend.config import get_settings

settings = get_settings()


def get_exchange():
	"""
	Buat instance exchange berdasarkan setting EXCHANGE di .env.
	Support: bybit, binance.
	Default: bybit (accessible dari Indonesia).
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
				"defaultType":           "spot",
				"fetchCurrencies":       False,
				"adjustForTimeDifference": True,
			},
		})

	raise ValueError(f"Exchange '{name}' not supported. Select: bybit, binance")


def fetch_ticker(symbol: str = None) -> dict:
	"""Ambil harga ticker terkini."""
	symbol   = symbol or settings.SYMBOL
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


def fetch_ohlcv(
	symbol: str = None,
	timeframe: str = None,
	limit: int = 500,
) -> list[dict]:
	"""
	Ambil data candlestick OHLCV.
	Args:
			symbol:    contoh 'BTC/USDT'
			timeframe: '1m','5m','15m','1h','4h','1d'
			limit:     jumlah candle (max 1000)
	"""
	symbol    = symbol    or settings.SYMBOL
	timeframe = timeframe or settings.TIMEFRAME
	exchange  = get_exchange()

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


def fetch_balance() -> dict:
	"""Ambil saldo akun. Butuh API key permission Read."""
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