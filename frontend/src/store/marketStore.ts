import { create } from 'zustand'
import type { Ticker, OHLCVCandle } from '../types'

interface MarketStore {
  // State
  ticker: Ticker | null
  candles: OHLCVCandle[]
  capital: number

  // Actions
  setTicker: (ticker: Ticker) => void
  setCandles: (candles: OHLCVCandle[]) => void
  setCapital: (capital: number) => void

  // Update harga dari WebSocket (lebih ringan dari replace seluruh ticker)
  updatePrice: (price: number, change_pct: number) => void
}

export const useMarketStore = create<MarketStore>((set, get) => ({
  ticker: null,
  candles: [],
  capital: 10000,

  setTicker: (ticker) => set({ ticker }),
  setCandles: (candles) => set({ candles }),
  setCapital: (capital) => set({ capital }),

  updatePrice: (price, change_pct) => {
    const current = get().ticker
    if (!current) return
    set({ ticker: { ...current, last: price, change_pct } })
  },
}))