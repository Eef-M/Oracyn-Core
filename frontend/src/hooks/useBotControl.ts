import { useCallback } from 'react'
import { useBotStore } from '../store/botStore'
import { startBot, stopBot, getBotStatus } from '../api/bot'

export function useBotControl() {
  const { status, isStarting, isStopping, setStatus, setStarting, setStopping } = useBotStore()

  const fetchStatus = useCallback(async () => {
    try {
      const data = await getBotStatus()
      setStatus(data)
    } catch (e) {
      console.error('[BotControl] fetchStatus error:', e)
    }
  }, [setStatus])

  const start = useCallback(async (paper = true) => {
    setStarting(true)
    try {
      await startBot(paper)
      await fetchStatus()
    } catch (e) {
      console.error('[BotControl] start error:', e)
    } finally {
      setStarting(false)
    }
  }, [fetchStatus, setStarting])

  const stop = useCallback(async () => {
    setStopping(true)
    try {
      await stopBot()
      await fetchStatus()
    } catch (e) {
      console.error('[BotControl] stop error:', e)
    } finally {
      setStopping(false)
    }
  }, [fetchStatus, setStopping])

  return {
    status,
    isStarting,
    isStopping,
    isRunning: status?.running ?? false,
    isPaper: status?.is_paper ?? true,
    capital: status?.capital ?? 0,
    start,
    stop,
    fetchStatus,
  }
}