import type { Signal } from "../types";

interface Props {
  signals: Signal[];
}

export function SignalLog({ signals }: Props) {
  if (signals.length === 0) {
    return (
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
        <h2 className="text-white font-medium mb-3">Signal Log</h2>
        <p className="text-zinc-600 text-sm text-center py-6">
          No signals yet. Start the bot first.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
      <h2 className="text-white font-medium mb-3">Signal Log</h2>
      <div className="space-y-1 max-h-64 overflow-y-auto pr-1">
        {signals.map((s) => {
          const dotColor =
            s.signal === "BUY"
              ? "bg-emerald-400"
              : s.signal === "SELL"
                ? "bg-red-400"
                : "bg-zinc-500";

          const textColor =
            s.signal === "BUY"
              ? "text-emerald-400"
              : s.signal === "SELL"
                ? "text-red-400"
                : "text-zinc-400";

          return (
            <div
              key={s.id}
              className="flex items-center gap-3 py-1.5 px-2 rounded-lg hover:bg-zinc-800/50 transition-colors"
            >
              <span
                className={`w-1.5 h-1.5 rounded-full shrink-0 ${dotColor}`}
              />
              <span className={`text-xs font-medium w-10 ${textColor}`}>
                {s.signal}
              </span>
              <span className="text-zinc-500 text-xs font-mono flex-1">
                ${s.price.toLocaleString("en-US", { minimumFractionDigits: 2 })}
              </span>
              <span className="text-zinc-600 text-xs">
                {(s.confidence * 100).toFixed(0)}%
              </span>
              <span className="text-zinc-700 text-xs">
                {new Date(s.created_at).toLocaleTimeString()}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
