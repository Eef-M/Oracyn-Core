import type { SignalType } from "../types";

interface Props {
  signal: SignalType;
  confidence: number;
  price: number;
  timestamp: string;
  indicators?: {
    rsi_14?: number;
    macd?: number;
    bb_pct?: number;
    volume_ratio?: number;
  };
}

export function SignalBadge({
  signal,
  confidence,
  price,
  timestamp,
  indicators,
}: Props) {
  const config = {
    BUY: {
      bg: "bg-emerald-500/15",
      border: "border-emerald-500/40",
      text: "text-emerald-400",
      label: "▲ BUY",
    },
    SELL: {
      bg: "bg-red-500/15",
      border: "border-red-500/40",
      text: "text-red-400",
      label: "▼ SELL",
    },
    HOLD: {
      bg: "bg-zinc-700/50",
      border: "border-zinc-600",
      text: "text-zinc-400",
      label: "— HOLD",
    },
  }[signal];

  const confidencePct = (confidence * 100).toFixed(1);
  const barColor =
    signal === "BUY"
      ? "bg-emerald-500"
      : signal === "SELL"
        ? "bg-red-500"
        : "bg-zinc-500";

  return (
    <div className={`rounded-xl border p-4 ${config.bg} ${config.border}`}>
      <div className="flex items-center justify-between mb-3">
        <span className={`text-lg font-bold ${config.text}`}>
          {config.label}
        </span>
        <span className="text-zinc-500 text-xs">
          {new Date(timestamp).toLocaleTimeString()}
        </span>
      </div>

      {/* Confidence bar */}
      <div className="mb-3">
        <div className="flex justify-between text-xs mb-1">
          <span className="text-zinc-500">Confidence</span>
          <span className={config.text}>{confidencePct}%</span>
        </div>
        <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${barColor}`}
            style={{ width: `${confidencePct}%` }}
          />
        </div>
      </div>

      {/* Price */}
      <div className="flex justify-between text-sm mb-3">
        <span className="text-zinc-500">Price</span>
        <span className="text-white font-mono">
          ${price.toLocaleString("en-US", { minimumFractionDigits: 2 })}
        </span>
      </div>

      {/* Indicators */}
      {indicators && (
        <div className="grid grid-cols-2 gap-x-4 gap-y-1 pt-3 border-t border-zinc-700/50">
          {indicators.rsi_14 !== undefined && (
            <>
              <span className="text-zinc-600 text-xs">RSI 14</span>
              <span
                className={`text-xs font-mono text-right ${
                  indicators.rsi_14 > 70
                    ? "text-red-400"
                    : indicators.rsi_14 < 30
                      ? "text-emerald-400"
                      : "text-zinc-300"
                }`}
              >
                {indicators.rsi_14.toFixed(1)}
              </span>
            </>
          )}
          {indicators.bb_pct !== undefined && (
            <>
              <span className="text-zinc-600 text-xs">BB %</span>
              <span className="text-xs font-mono text-right text-zinc-300">
                {(indicators.bb_pct * 100).toFixed(1)}%
              </span>
            </>
          )}
          {indicators.volume_ratio !== undefined && (
            <>
              <span className="text-zinc-600 text-xs">Volume ratio</span>
              <span
                className={`text-xs font-mono text-right ${
                  indicators.volume_ratio > 2
                    ? "text-amber-400"
                    : "text-zinc-300"
                }`}
              >
                {indicators.volume_ratio.toFixed(2)}x
              </span>
            </>
          )}
        </div>
      )}
    </div>
  );
}
