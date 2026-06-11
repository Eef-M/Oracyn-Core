import client from './client'
import type { BotStatus } from '../types'

export const getBotStatus = async (): Promise<BotStatus> => {
  const { data } = await client.get('/bot/status')
  return data
}

export const startBot = async (paper = true): Promise<{ status: string; mode: string }> => {
  const { data } = await client.post(`/bot/start?paper=${paper}`)
  return data
}

export const stopBot = async (): Promise<{ status: string }> => {
  const { data } = await client.post('/bot/stop')
  return data
}

export const getMLStatus = async (): Promise<{ model_exists: boolean; message: string }> => {
  const { data } = await client.get('/ml/status')
  return data
}

export const trainModel = async (limit = 1000, timeframe = '1h') => {
  const { data } = await client.post(`/ml/train?limit=${limit}&timeframe=${timeframe}`)
  return data
}

export const getLatestSignal = async () => {
  const { data } = await client.get('/ml/predict')
  return data
}