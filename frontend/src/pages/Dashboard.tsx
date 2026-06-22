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

  useWebSocket();

  const { fetchStatus } = useBotControl();
  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const { setCandles } = useMarketStore();

  const {
    data: candles = [],
    isError: candlesError,
    error: candlesErrorObj,
  } = useQuery<OHLCVCandle[]>({
    queryKey: ["ohlcv", timeframe],
    queryFn: () => getOHLCV(timeframe, 200),
    refetchInterval: 60_000,
    retry: 2, // beri kesempatan retry kalau proxy glitch
  });

  const { data: trades = [] } = useQuery({
    queryKey: ["trades"],
    queryFn: () => getTrades(50),
    refetchInterval: 45_000,
    retry: 2,
  });

  const { data: signals = [] } = useQuery({
    queryKey: ["signals"],
    queryFn: () => getSignals(30),
    refetchInterval: 30_000,
    retry: 2,
  });

  const { data: performance = null } = useQuery({
    queryKey: ["performance"],
    queryFn: getPerformance,
    refetchInterval: 120_000,
    retry: 2,
  });

  const { data: latestSignal = null } = useQuery({
    queryKey: ["latestSignal"],
    queryFn: getLatestSignal,
    refetchInterval: 60_000,
    retry: 2,
  });

  useEffect(() => {
    if (candles.length > 0) setCandles(candles);
  }, [candles, setCandles]);

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      <div className="max-w-screen-2xl mx-auto px-4 py-6 space-y-4">
        <StatsCards performance={performance} />

        <div className="grid grid-cols-1 xl:grid-cols-4 gap-4">
          <div className="xl:col-span-3">
            {candlesError ? (
              <div className="bg-zinc-950 border border-red-900/50 rounded-xl p-8 text-center">
                <p className="text-red-400 text-sm mb-1">
                  Gagal memuat data chart
                </p>
                <p className="text-zinc-600 text-xs">
                  {(candlesErrorObj as Error)?.message ?? "Unknown error"}
                </p>
              </div>
            ) : candles.length === 0 ? (
              <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-8 text-center">
                <p className="text-zinc-500 text-sm">Loading chart data...</p>
              </div>
            ) : (
              <CandlestickChart
                candles={candles}
                symbol="BTC/USDT"
                timeframe={timeframe}
                onTimeframeChange={setTimeframe}
              />
            )}
          </div>
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
