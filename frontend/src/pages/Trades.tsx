import { useQuery } from "@tanstack/react-query";
import { getTrades, getPerformance } from "../api/trades";
import { TradeHistory } from "../components/TradeHistory";
import { PnLChart } from "../components/PnLChart";

export function Trades() {
  const { data: trades = [], isLoading } = useQuery({
    queryKey: ["trades", "all"],
    queryFn: () => getTrades(200),
    refetchInterval: 30_000,
  });

  const { data: performance } = useQuery({
    queryKey: ["performance"],
    queryFn: getPerformance,
    refetchInterval: 60_000,
  });

  const closedTrades = trades.filter((t) => t.status === "CLOSED");
  const openTrades = trades.filter((t) => t.status === "OPEN");
  const winTrades = closedTrades.filter((t) => (t.pnl ?? 0) > 0);
  const totalPnl = closedTrades.reduce((sum, t) => sum + (t.pnl ?? 0), 0);

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      <div className="max-w-7xl mx-auto px-4 py-6 space-y-4">
        <h1 className="text-xl font-semibold text-white">Trade History</h1>

        {/* Summary cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: "Total Trades", value: closedTrades.length.toString() },
            { label: "Open Positions", value: openTrades.length.toString() },
            {
              label: "Win Rate",
              value:
                closedTrades.length > 0
                  ? `${((winTrades.length / closedTrades.length) * 100).toFixed(1)}%`
                  : "—",
            },
            {
              label: "Total PnL",
              value: `${totalPnl >= 0 ? "+" : ""}$${totalPnl.toFixed(2)}`,
              color: totalPnl >= 0 ? "text-emerald-400" : "text-red-400",
            },
          ].map((card) => (
            <div
              key={card.label}
              className="bg-zinc-900 border border-zinc-800 rounded-xl p-4"
            >
              <p className="text-zinc-500 text-xs mb-1">{card.label}</p>
              <p
                className={`text-xl font-semibold font-mono ${card.color ?? "text-white"}`}
              >
                {card.value}
              </p>
            </div>
          ))}
        </div>

        {/* PnL Chart */}
        <PnLChart trades={trades} />

        {/* Trade table */}
        {isLoading ? (
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-8 text-center">
            <p className="text-zinc-500 text-sm">Loading trades...</p>
          </div>
        ) : (
          <TradeHistory trades={trades} />
        )}

        {/* Sharpe & drawdown info */}
        {performance && (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {[
              {
                label: "Sharpe Ratio",
                value: performance.sharpe_ratio.toFixed(2),
              },
              {
                label: "Max Drawdown",
                value: `${(performance.max_drawdown * 100).toFixed(2)}%`,
              },
              {
                label: "Avg PnL/Trade",
                value: `${(performance.avg_pnl_pct * 100).toFixed(3)}%`,
              },
            ].map((s) => (
              <div
                key={s.label}
                className="bg-zinc-900 border border-zinc-800 rounded-xl p-4"
              >
                <p className="text-zinc-500 text-xs mb-1">{s.label}</p>
                <p className="text-white font-mono font-semibold">{s.value}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
