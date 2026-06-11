import client from './client'
import type { Ticker, OHLCVCandle } from '../types'

export const getTicker = async (symbol?: string): Promise<Ticker> => {
  const params = symbol ? `?symbol=${symbol}` : ''
  const { data } = await client.get(`/ticker${params}`)
  return data
}

export const getOHLCV = async (
  timeframe = '1h',
  limit = 200,
  refresh = false
): Promise<OHLCVCandle[]> => {
  const { data } = await client.get(
    `/ohlcv?timeframe=${timeframe}&limit=${limit}&refresh=${refresh}`
  )
  return data
}