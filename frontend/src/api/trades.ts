import client from './client'
import type { Trade, Signal, PerformanceStats } from '../types'

export const getTrades = async (limit = 50): Promise<Trade[]> => {
  const { data } = await client.get(`/trades?limit=${limit}`)
  return data
}

export const getSignals = async (limit = 20): Promise<Signal[]> => {
  const { data } = await client.get(`/signals?limit=${limit}`)
  return data
}

export const getPerformance = async (): Promise<PerformanceStats> => {
  const { data } = await client.get('/performance')
  return data
}