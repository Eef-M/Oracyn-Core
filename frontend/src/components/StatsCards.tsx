import { useMarketStore } from "../store/marketStore";
import { useBotStore } from "../store/botStore";
import type { PerformanceStats } from "../types";

interface Props {
  performance: PerformanceStats | null;
}

function StatCard({
  label,
  value,
  sub,
  color = "white",
}: {
  label: string;
  value: string;
  sub?: string;
  color?: "white" | "green" | "red" | "yellow" | "indigo";
}) {
  const colorMap = {
    white: "text-white",
    green: "text-emerald-400",
    red: "text-red-400",
    yellow: "text-amber-400",
    indigo: "text-indigo-400",
  };
  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
      <p className="text-zinc-500 text-xs mb-1">{label}</p>
      <p className={`text-xl font-semibold font-mono ${colorMap[color]}`}>
        {value}
      </p>
      {sub && <p className="text-zinc-600 text-xs mt-1">{sub}</p>}
    </div>
  );
}

export function StatsCards({ performance }: Props) {
  const capital = useMarketStore((s) => s.capital);
  const ticker = useMarketStore((s) => s.ticker);
  const status = useBotStore((s) => s.status);

  const totalPnl = performance?.total_pnl ?? 0;
  const winRate = performance?.win_rate ?? 0;
  const sharpe = performance?.sharpe_ratio ?? 0;
  const maxDrawdown = performance?.max_drawdown ?? 0;
  const totalTrades = performance?.total_trades ?? 0;

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
      <StatCard
        label="Capital"
        value={`$${capital.toLocaleString("en-US", { minimumFractionDigits: 2 })}`}
        sub={status?.is_paper ? "Paper trading" : "Live trading"}
        color="indigo"
      />
      <StatCard
        label="Total PnL"
        value={`${totalPnl >= 0 ? "+" : ""}$${totalPnl.toFixed(2)}`}
        sub={`${(performance?.total_pnl_pct ?? 0 * 100).toFixed(2)}%`}
        color={totalPnl >= 0 ? "green" : "red"}
      />
      <StatCard
        label="Win Rate"
        value={`${(winRate * 100).toFixed(1)}%`}
        sub={`${totalTrades} trades`}
        color={winRate >= 0.5 ? "green" : "yellow"}
      />
      <StatCard
        label="Sharpe Ratio"
        value={sharpe.toFixed(2)}
        sub="Annualized"
        color={sharpe >= 1 ? "green" : sharpe >= 0 ? "yellow" : "red"}
      />
      <StatCard
        label="Max Drawdown"
        value={`${(maxDrawdown * 100).toFixed(2)}%`}
        color={maxDrawdown > -0.15 ? "yellow" : "red"}
      />
      <StatCard
        label="24h Volume"
        value={ticker ? `${ticker.volume.toFixed(1)} BTC` : "—"}
        sub={ticker ? `H: $${ticker.high.toLocaleString()}` : ""}
        color="white"
      />
    </div>
  );
}
