import { useEffect, useRef, useState } from "react";
import {
  CandlestickSeries,
  createChart,
  LineSeries,
  type IChartApi,
  type ISeriesApi,
  type CandlestickData,
  type Time,
  ColorType,
} from "lightweight-charts";
import type { OHLCVCandle } from "../types";

// Fix #5 — konstanta menggantikan magic numbers & hardcoded colors
const CHART_COLORS = {
  background: "#09090b",
  text: "#71717a",
  grid: "#18181b",
  crosshair: "#52525b",
  border: "#27272a",
  candleUp: "#10b981",
  candleDown: "#ef4444",
  ema20: "#6366f1",
  ema50: "#f59e0b",
} as const;

const EMA_PERIODS = { short: 20, long: 50 } as const;
const CHART_HEIGHT = 380;

// Fix #1 — TF type guard menggantikan type assertion
const VALID_TIMEFRAMES = ["1h", "4h", "1d"] as const;
type TF = (typeof VALID_TIMEFRAMES)[number];

function isValidTF(value: string): value is TF {
  return (VALID_TIMEFRAMES as readonly string[]).includes(value);
}

interface Props {
  candles: OHLCVCandle[];
  symbol?: string;
  timeframe?: string;
  // Fix #7 — callback untuk beri tahu parent saat timeframe berubah
  onTimeframeChange?: (tf: TF) => void;
}

export function CandlestickChart({
  candles,
  symbol = "BTC/USDT",
  timeframe = "1h",
  onTimeframeChange,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleRef = useRef<ISeriesApi<"Candlestick", Time> | null>(null);
  const ema20Ref = useRef<ISeriesApi<"Line", Time> | null>(null);
  const ema50Ref = useRef<ISeriesApi<"Line", Time> | null>(null);

  // Fix #1 — pakai type guard, bukan type assertion
  const initialTF = isValidTF(timeframe) ? timeframe : "1h";
  const [activeTF, setActiveTF] = useState<TF>(initialTF);
  const [showEMA, setShowEMA] = useState(true);

  // Fix #7 — sync activeTF ke parent & bisa dipakai untuk trigger fetch
  const handleTFChange = (tf: TF) => {
    setActiveTF(tf);
    onTimeframeChange?.(tf);
  };

  // Inisialisasi chart sekali saat mount
  useEffect(() => {
    if (!containerRef.current) return;

    // Fix #6 — bungkus createChart dalam try-catch
    let chart: IChartApi;
    try {
      chart = createChart(containerRef.current, {
        layout: {
          background: { type: ColorType.Solid, color: CHART_COLORS.background },
          textColor: CHART_COLORS.text,
        },
        grid: {
          vertLines: { color: CHART_COLORS.grid },
          horzLines: { color: CHART_COLORS.grid },
        },
        crosshair: {
          vertLine: { color: CHART_COLORS.crosshair, width: 1, style: 2 },
          horzLine: { color: CHART_COLORS.crosshair, width: 1, style: 2 },
        },
        rightPriceScale: { borderColor: CHART_COLORS.border },
        timeScale: { borderColor: CHART_COLORS.border, timeVisible: true },
        width: containerRef.current.clientWidth,
        height: CHART_HEIGHT,
      });
    } catch (err) {
      console.error("[CandlestickChart] Failed to create chart:", err);
      return;
    }

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: CHART_COLORS.candleUp,
      downColor: CHART_COLORS.candleDown,
      borderUpColor: CHART_COLORS.candleUp,
      borderDownColor: CHART_COLORS.candleDown,
      wickUpColor: CHART_COLORS.candleUp,
      wickDownColor: CHART_COLORS.candleDown,
    });

    const ema20Series = chart.addSeries(LineSeries, {
      color: CHART_COLORS.ema20,
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
    });

    const ema50Series = chart.addSeries(LineSeries, {
      color: CHART_COLORS.ema50,
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
    });

    chartRef.current = chart;
    candleRef.current = candleSeries;
    ema20Ref.current = ema20Series;
    ema50Ref.current = ema50Series;

    // Fix #2 — ResizeObserver juga handle initial width yang tidak stabil
    const observer = new ResizeObserver((entries) => {
      const width = entries[0]?.contentRect.width;
      if (width) chart.applyOptions({ width });
    });
    observer.observe(containerRef.current);

    return () => {
      observer.disconnect();
      chart.remove();
    };
  }, []);

  // Update data saat candles berubah
  useEffect(() => {
    if (!candleRef.current || !ema20Ref.current || !ema50Ref.current) return;
    if (candles.length === 0) return;

    const candleData: CandlestickData[] = candles.map((c) => ({
      time: (new Date(c.timestamp).getTime() / 1000) as Time,
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close,
    }));
    candleRef.current.setData(candleData);

    const closes = candles.map((c) => c.close);
    if (showEMA) {
      ema20Ref.current.setData(calcEMA(closes, candles, EMA_PERIODS.short));
      ema50Ref.current.setData(calcEMA(closes, candles, EMA_PERIODS.long));
    } else {
      ema20Ref.current.setData([]);
      ema50Ref.current.setData([]);
    }

    chartRef.current?.timeScale().fitContent();
  }, [candles, showEMA]);

  return (
    <div className="bg-zinc-950 border border-zinc-800 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800">
        <div className="flex items-center gap-2">
          <span className="text-white font-medium text-sm">{symbol}</span>
          <span className="text-zinc-600 text-xs">Candlestick</span>
        </div>

        <div className="flex items-center gap-3">
          {/* Fix #7 — timeframe buttons sekarang fungsional */}
          <div className="flex gap-1">
            {VALID_TIMEFRAMES.map((tf) => (
              <button
                key={tf}
                onClick={() => handleTFChange(tf)}
                className={`px-2 py-0.5 rounded text-xs font-medium transition-colors ${
                  activeTF === tf
                    ? "bg-indigo-600 text-white"
                    : "text-zinc-500 hover:text-zinc-300"
                }`}
              >
                {tf}
              </button>
            ))}
          </div>

          {/* EMA toggle */}
          <button
            onClick={() => setShowEMA(!showEMA)}
            className="flex items-center gap-1.5 text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
          >
            <span
              className={`w-2 h-2 rounded-full ${showEMA ? "bg-indigo-500" : "bg-zinc-700"}`}
            />
            EMA
          </button>

          {showEMA && (
            <div className="flex items-center gap-3 text-xs">
              <span className="flex items-center gap-1">
                <span className="w-3 h-px bg-indigo-500 inline-block" />
                <span className="text-zinc-500">EMA{EMA_PERIODS.short}</span>
              </span>
              <span className="flex items-center gap-1">
                <span className="w-3 h-px bg-amber-500 inline-block" />
                <span className="text-zinc-500">EMA{EMA_PERIODS.long}</span>
              </span>
            </div>
          )}
        </div>
      </div>

      <div ref={containerRef} className="w-full" />
    </div>
  );
}

// ── Helpers ───────────────────────────────────────────────

function calcEMA(
  closes: number[],
  candles: OHLCVCandle[],
  period: number,
): { time: Time; value: number }[] {
  // Fix #3 — guard kalau closes kosong
  if (closes.length === 0) return [];

  const k = 2 / (period + 1);
  const result: { time: Time; value: number }[] = [];

  // Fix #4 — hapus redundansi if (i===0) di dalam loop
  // inisialisasi ema di luar loop sudah cukup
  let ema = closes[0];

  closes.forEach((price, i) => {
    ema = price * k + ema * (1 - k);

    if (i >= period - 1) {
      result.push({
        time: (new Date(candles[i].timestamp).getTime() / 1000) as Time,
        value: ema,
      });
    }
  });

  return result;
}
