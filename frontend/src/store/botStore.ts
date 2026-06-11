import { create } from 'zustand'
import type { BotStatus, Signal } from '../types'

interface BotStore {
  // State
  status: BotStatus | null
  lastSignal: Signal | null
  isStarting: boolean
  isStopping: boolean

  // Actions
  setStatus: (status: BotStatus) => void
  setLastSignal: (signal: Signal) => void
  setStarting: (v: boolean) => void
  setStopping: (v: boolean) => void
}

export const useBotStore = create<BotStore>((set) => ({
  status: null,
  lastSignal: null,
  isStarting: false,
  isStopping: false,

  setStatus: (status) => set({ status }),
  setLastSignal: (signal) => set({ lastSignal: signal }),
  setStarting: (v) => set({ isStarting: v }),
  setStopping: (v) => set({ isStopping: v }),
}))