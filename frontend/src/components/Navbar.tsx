import { useBotStore } from "../store/botStore";
import { useMarketStore } from "../store/marketStore";

export function Navbar() {
  const status = useBotStore((s) => s.status);
  const ticker = useMarketStore((s) => s.ticker);

  const isRunning = status?.running ?? false;
  const isPaper = status?.is_paper ?? true;

  return (
    <nav className="border-b border-zinc-800 bg-zinc-950 px-6 py-3 flex items-center justify-between">
      {/* Logo */}
      <div className="flex items-center gap-3">
        <div className="w-7 h-7 rounded-lg bg-indigo-600 flex items-center justify-center">
          <span className="text-white text-xs font-bold">OC</span>
        </div>
        <span className="text-white font-semibold tracking-wide">
          Oracyn Core
        </span>
      </div>

      {/* Center — Live price */}
      {ticker && (
        <div className="flex items-center gap-2">
          <span className="text-zinc-400 text-sm">{ticker.symbol}</span>
          <span className="text-white font-mono font-semibold">
            ${ticker.last.toLocaleString("en-US", { minimumFractionDigits: 2 })}
          </span>
          <span
            className={`text-sm font-medium ${ticker.change_pct >= 0 ? "text-emerald-400" : "text-red-400"}`}
          >
            {ticker.change_pct >= 0 ? "+" : ""}
            {ticker.change_pct.toFixed(2)}%
          </span>
        </div>
      )}

      {/* Right — status bot */}
      <div className="flex items-center gap-3">
        {isPaper && (
          <span className="text-xs px-2 py-1 rounded bg-amber-500/20 text-amber-400 font-medium">
            PAPER
          </span>
        )}
        <div className="flex items-center gap-2">
          <span
            className={`w-2 h-2 rounded-full ${isRunning ? "bg-emerald-400 animate-pulse" : "bg-zinc-600"}`}
          />
          <span
            className={`text-sm ${isRunning ? "text-emerald-400" : "text-zinc-500"}`}
          >
            {isRunning ? "Running" : "Stopped"}
          </span>
        </div>
      </div>
    </nav>
  );
}
