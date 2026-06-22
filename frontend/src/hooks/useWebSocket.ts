import { useEffect, useRef } from 'react'
import { useMarketStore } from '../store/marketStore'
import { useBotStore } from '../store/botStore'
import type { LiveUpdate } from '../types'

const WS_URL = 'ws://localhost:8000/ws/live'
const RECONNECT_DELAY = 3000

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTmRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const isMountedRef = useRef(false)

  const updatePrice = useMarketStore((s) => s.updatePrice)
  const setCapital = useMarketStore((s) => s.setCapital)
  const setStatus = useBotStore((s) => s.setStatus)

  const actionsRef = useRef({ updatePrice, setCapital, setStatus })

  useEffect(() => {
    actionsRef.current = { updatePrice, setCapital, setStatus }
  })

  useEffect(() => {
    isMountedRef.current = true

    function connect() {
      if (!isMountedRef.current) return
      if (wsRef.current && wsRef.current.readyState <= WebSocket.OPEN) return

      try {
        const socket = new WebSocket(WS_URL)
        wsRef.current = socket

        socket.onopen = () => {
          if (!isMountedRef.current) { socket.close(); return }
          console.log('[WS] Connected')
        }

        socket.onmessage = (event) => {
          if (!isMountedRef.current) return
          try {
            const data: LiveUpdate = JSON.parse(event.data)
            if (data.type !== 'live_update') return

            const { updatePrice, setCapital, setStatus } = actionsRef.current
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
          } catch (e) {
            console.error('[WS] Parse error:', e)
          }
        }

        socket.onclose = () => {
          if (!isMountedRef.current) return
          console.log('[WS] Disconnected — reconnecting...')
          reconnectTmRef.current = setTimeout(connect, RECONNECT_DELAY)
        }

        socket.onerror = () => {
          // onclose dipanggil otomatis setelah onerror
        }

      } catch (e) {
        console.error('[WS] Connection failed:', e)
        if (isMountedRef.current) {
          reconnectTmRef.current = setTimeout(connect, RECONNECT_DELAY)
        }
      }
    }

    connect()

    return () => {
      isMountedRef.current = false

      if (reconnectTmRef.current) {
        clearTimeout(reconnectTmRef.current)
        reconnectTmRef.current = null
      }

      if (wsRef.current) {
        wsRef.current.onclose = null
        wsRef.current.onerror = null
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps
}