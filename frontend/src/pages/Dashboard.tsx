import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { useWebSocket } from "../hooks/useWebSocket";
import { useBotControl } from "../hooks/useBotControl";
import { useMarketStore } from "../store/marketStore";

import { getOHLCV } from "../api/market";
import { getTrades, getSignals, getPerformance } from "../api/trades";
import { getLatestSignal } from "../api/bot";

import { StatsCards } from "../components/StatsCards";
import { BotControls } from "../components/BotControls";
import { CandlestickChart } from "../components/CandlestickChart";
import { PnLChart } from "../components/PnLChart";
import { SignalBadge } from "../components/SignalBadge";
import { SignalLog } from "../components/SignalLog";
import { TradeHistory } from "../components/TradeHistory";
import { IndicatorPanel } from "../components/IndicatorPanel";

import type { OHLCVCandle } from "../types";

export function Dashboard() {
  const [timeframe, setTimeframe] = useState("1h");

  // Aktifkan WebSocket — update store otomatis
  useWebSocket();

  // Sync bot status saat mount
  const { fetchStatus } = useBotControl();
  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  // Sync ticker awal dari REST (sebelum WS connect)
  const { setCandles } = useMarketStore();

  // ── Data fetching dengan React Query ─────────────────────
  const { data: candles = [] } = useQuery<OHLCVCandle[]>({
    queryKey: ["ohlcv", timeframe],
    queryFn: () => getOHLCV(timeframe, 200),
    refetchInterval: 60_000, // refresh tiap 1 menit
  });

  const { data: trades = [] } = useQuery({
    queryKey: ["trades"],
    queryFn: () => getTrades(50),
    refetchInterval: 30_000,
  });

  const { data: signals = [] } = useQuery({
    queryKey: ["signals"],
    queryFn: () => getSignals(30),
    refetchInterval: 30_000,
  });

  const { data: performance = null } = useQuery({
    queryKey: ["performance"],
    queryFn: getPerformance,
    refetchInterval: 60_000,
  });

  const { data: latestSignal = null } = useQuery({
    queryKey: ["latestSignal"],
    queryFn: getLatestSignal,
    refetchInterval: 60_000,
  });

  // Sync candles ke store saat data berubah
  useEffect(() => {
    if (candles.length > 0) setCandles(candles);
  }, [candles, setCandles]);

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      <div className="max-w-screen-2xl mx-auto px-4 py-6 space-y-4">
        {/* Row 1 — Stats */}
        <StatsCards performance={performance} />

        {/* Row 2 — Chart + Right panel */}
        <div className="grid grid-cols-1 xl:grid-cols-4 gap-4">
          {/* Candlestick chart — 3/4 width */}
          <div className="xl:col-span-3">
            <CandlestickChart
              candles={candles}
              symbol="BTC/USDT"
              timeframe={timeframe}
              onTimeframeChange={setTimeframe}
            />
          </div>

          {/* Right panel — 1/4 width */}
          <div className="flex flex-col gap-4">
            <BotControls />

            {latestSignal && (
              <SignalBadge
                signal={latestSignal.signal}
                confidence={latestSignal.confidence}
                price={latestSignal.price}
                timestamp={latestSignal.timestamp}
                indicators={latestSignal.indicators}
              />
            )}
          </div>
        </div>

        {/* Row 3 — Indicators + Signal Log */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          <IndicatorPanel
            rsi={latestSignal?.indicators?.rsi_14}
            macd={latestSignal?.indicators?.macd}
            macdSignal={latestSignal?.indicators?.macd_signal}
            bbPct={latestSignal?.indicators?.bb_pct}
            volumeRatio={latestSignal?.indicators?.volume_ratio}
            atrPct={latestSignal?.indicators?.atr_pct}
          />
          <div className="xl:col-span-2">
            <SignalLog signals={signals} />
          </div>
        </div>

        {/* Row 4 — PnL Chart + Trade History */}
        <div className="grid grid-cols-1 xl:grid-cols-5 gap-4">
          <div className="xl:col-span-2">
            <PnLChart trades={trades} />
          </div>
          <div className="xl:col-span-3">
            <TradeHistory trades={trades} />
          </div>
        </div>
      </div>
    </div>
  );
}
