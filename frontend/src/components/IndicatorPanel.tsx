interface Props {
  rsi?: number;
  macd?: number;
  macdSignal?: number;
  bbPct?: number;
  volumeRatio?: number;
  atrPct?: number;
}

function GaugeBar({
  value,
  min,
  max,
  label,
  lowGood = false,
}: {
  value: number;
  min: number;
  max: number;
  label: string;
  lowGood?: boolean;
}) {
  const pct = Math.min(100, Math.max(0, ((value - min) / (max - min)) * 100));
  const isHigh = pct > 70;
  const isLow = pct < 30;
  const color = lowGood
    ? isLow
      ? "bg-emerald-500"
      : isHigh
        ? "bg-red-500"
        : "bg-amber-500"
    : isHigh
      ? "bg-red-500"
      : isLow
        ? "bg-emerald-500"
        : "bg-indigo-500";

  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-zinc-500">{label}</span>
        <span className="text-zinc-300 font-mono">{value.toFixed(2)}</span>
      </div>
      <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export function IndicatorPanel({
  rsi = 50,
  macd = 0,
  macdSignal = 0,
  bbPct = 0.5,
  volumeRatio = 1,
  atrPct = 0,
}: Props) {
  const macdColor = macd > macdSignal ? "text-emerald-400" : "text-red-400";
  const macdLabel = macd > macdSignal ? "▲ Bullish" : "▼ Bearish";

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
      <h2 className="text-white font-medium mb-4">Indicators</h2>

      <div className="space-y-4">
        {/* RSI */}
        <div>
          <GaugeBar value={rsi} min={0} max={100} label="RSI (14)" />
          <div className="flex justify-between text-xs mt-1">
            <span className="text-zinc-700">Oversold</span>
            <span
              className={
                rsi > 70
                  ? "text-red-400"
                  : rsi < 30
                    ? "text-emerald-400"
                    : "text-zinc-600"
              }
            >
              {rsi > 70 ? "Overbought" : rsi < 30 ? "Oversold" : "Neutral"}
            </span>
            <span className="text-zinc-700">Overbought</span>
          </div>
        </div>

        {/* MACD */}
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-zinc-500">MACD</span>
            <span className={`${macdColor} font-medium`}>{macdLabel}</span>
          </div>
          <div className="flex gap-2 text-xs">
            <div className="flex-1 bg-zinc-800 rounded px-2 py-1">
              <span className="text-zinc-600">MACD </span>
              <span className="font-mono text-zinc-300">{macd.toFixed(2)}</span>
            </div>
            <div className="flex-1 bg-zinc-800 rounded px-2 py-1">
              <span className="text-zinc-600">Signal </span>
              <span className="font-mono text-zinc-300">
                {macdSignal.toFixed(2)}
              </span>
            </div>
          </div>
        </div>

        {/* Bollinger Band % */}
        <div>
          <GaugeBar
            value={bbPct * 100}
            min={0}
            max={100}
            label="BB Position %"
          />
          <div className="flex justify-between text-xs mt-1">
            <span className="text-zinc-700">Lower band</span>
            <span className="text-zinc-700">Upper band</span>
          </div>
        </div>

        {/* Volume ratio */}
        <div>
          <GaugeBar value={volumeRatio} min={0} max={3} label="Volume Ratio" />
          <p className="text-zinc-700 text-xs mt-1">
            {volumeRatio > 2 ? "⚡ Volume spike terdeteksi" : "Volume normal"}
          </p>
        </div>

        {/* ATR % */}
        {atrPct > 0 && (
          <div>
            <div className="flex justify-between text-xs">
              <span className="text-zinc-500">ATR %</span>
              <span className="font-mono text-zinc-300">
                {(atrPct * 100).toFixed(2)}%
              </span>
            </div>
            <p className="text-zinc-600 text-xs mt-1">Volatilitas saat ini</p>
          </div>
        )}
      </div>
    </div>
  );
}
