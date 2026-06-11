import { useEffect, useRef, useCallback } from 'react'
import { useMarketStore } from '../store/marketStore'
import { useBotStore } from '../store/botStore'
import type { LiveUpdate } from '../types'

const WS_URL = 'ws://localhost:8000/ws/live'
const RECONNECT_DELAY = 3000

export function useWebSocket() {
  const ws = useRef<WebSocket | null>(null)
  const reconnect = useRef<ReturnType<typeof setTimeout> | null>(null)
  const isClosing = useRef(false)

  // Use selectors to ensure stable function references and prevent reconnection loops
  const updatePrice = useMarketStore((state) => state.updatePrice)
  const setCapital = useMarketStore((state) => state.setCapital)
  const setStatus = useBotStore((state) => state.setStatus)

  // Didefinisikan dengan useCallback sebelum useEffect agar tidak ada
  // "accessed before declared" error di TypeScript strict mode
  const connect = useCallback(function connectImpl() {
    if (isClosing.current) return
    try {
      ws.current = new WebSocket(WS_URL)

      ws.current.onopen = () => {
        console.log('[WS] Connected')
      }

      ws.current.onmessage = (event) => {
        try {
          const data: LiveUpdate = JSON.parse(event.data)

          if (data.type === 'live_update') {
            updatePrice(data.price, data.change_pct)

            if (data.bot) {
              setCapital(data.bot.capital)
              setStatus({
                running: data.bot.running,
                is_paper: data.bot.is_paper,
                symbol: data.symbol,
                timeframe: '1h',
                capital: data.bot.capital,
              })
            }
          } else if (data.type === 'error') {
            console.error('[WS] Server error:', data.message)
          }
        } catch (e) {
          console.error('[WS] Parse error:', e)
        }
      }

      ws.current.onclose = () => {
        if (isClosing.current) return
        console.log('[WS] Disconnected — reconnecting...')
        reconnect.current = setTimeout(connectImpl, RECONNECT_DELAY)
      }

      ws.current.onerror = (err) => {
        console.error('[WS] Error:', err)
        ws.current?.close()
      }

    } catch (e) {
      console.error('[WS] Connection failed:', e)
      reconnect.current = setTimeout(connectImpl, RECONNECT_DELAY)
    }
  }, [updatePrice, setCapital, setStatus])

  useEffect(() => {
    isClosing.current = false
    connect()
    return () => {
      isClosing.current = true
      if (reconnect.current) clearTimeout(reconnect.current)
      ws.current?.close()
    }
  }, [connect])
}