import type { Trade } from "../types";

interface Props {
  trades: Trade[];
}

export function TradeHistory({ trades }: Props) {
  if (trades.length === 0) {
    return (
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
        <h2 className="text-white font-medium mb-3">Trade History</h2>
        <p className="text-zinc-600 text-sm text-center py-6">
          No trades recorded yet.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-white font-medium">Trade History</h2>
        <span className="text-zinc-600 text-xs">{trades.length} trades</span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-zinc-600 text-xs border-b border-zinc-800">
              <th className="text-left pb-2 font-medium">Action</th>
              <th className="text-right pb-2 font-medium">Entry</th>
              <th className="text-right pb-2 font-medium">Exit</th>
              <th className="text-right pb-2 font-medium">Qty</th>
              <th className="text-right pb-2 font-medium">PnL</th>
              <th className="text-right pb-2 font-medium">Status</th>
              <th className="text-right pb-2 font-medium">Time</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/50">
            {trades.map((trade) => {
              const pnlPositive = (trade.pnl ?? 0) >= 0;
              return (
                <tr
                  key={trade.id}
                  className="hover:bg-zinc-800/30 transition-colors"
                >
                  {/* Action */}
                  <td className="py-2">
                    <span
                      className={`text-xs font-medium px-1.5 py-0.5 rounded ${
                        trade.action === "BUY"
                          ? "bg-emerald-500/20 text-emerald-400"
                          : "bg-red-500/20 text-red-400"
                      }`}
                    >
                      {trade.action}
                    </span>
                  </td>

                  {/* Entry */}
                  <td className="py-2 text-right font-mono text-zinc-300 text-xs">
                    ${trade.entry_price.toLocaleString()}
                  </td>

                  {/* Exit */}
                  <td className="py-2 text-right font-mono text-zinc-500 text-xs">
                    {trade.exit_price
                      ? `$${trade.exit_price.toLocaleString()}`
                      : "—"}
                  </td>

                  {/* Quantity */}
                  <td className="py-2 text-right font-mono text-zinc-400 text-xs">
                    {trade.quantity.toFixed(5)}
                  </td>

                  {/* PnL */}
                  <td
                    className={`py-2 text-right font-mono text-xs ${
                      trade.pnl === null
                        ? "text-zinc-600"
                        : pnlPositive
                          ? "text-emerald-400"
                          : "text-red-400"
                    }`}
                  >
                    {trade.pnl === null
                      ? "—"
                      : `${pnlPositive ? "+" : ""}$${trade.pnl.toFixed(2)}`}
                  </td>

                  {/* Status */}
                  <td className="py-2 text-right">
                    <span
                      className={`text-xs px-1.5 py-0.5 rounded ${
                        trade.status === "OPEN"
                          ? "bg-indigo-500/20 text-indigo-400"
                          : "bg-zinc-700 text-zinc-500"
                      }`}
                    >
                      {trade.status}
                    </span>
                  </td>

                  {/* Time */}
                  <td className="py-2 text-right text-zinc-600 text-xs">
                    {new Date(trade.opened_at).toLocaleString("en-US", {
                      month: "short",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
