import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import type { Trade } from "../types";

interface DataPoint {
  label: string; // Fix #5 — pakai label dengan jam untuk hindari duplikat
  cumulative: number;
  pnl: number; // PnL per trade tersedia di data
}

// Fix #3 — hapus non-null assertion, pakai optional chaining yang aman
function buildEquityCurve(trades: Trade[]): DataPoint[] {
  const closed = trades
    .filter(
      (t): t is Trade & { pnl: number; closed_at: string } =>
        t.status === "CLOSED" && t.pnl !== null && t.closed_at !== null,
    )
    .sort(
      (a, b) =>
        new Date(a.closed_at).getTime() - new Date(b.closed_at).getTime(),
    );

  let cumulative = 0;
  return closed.map((t) => {
    cumulative += t.pnl;

    // Fix #5 — sertakan jam:menit agar tidak duplikat di hari yang sama
    const date = new Date(t.closed_at);
    const label =
      date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
      }) +
      " " +
      date.toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
      });

    return {
      label,
      // Fix #6 — rounding dilakukan sekali di sini, bukan parseFloat(x.toFixed(2))
      cumulative: Math.round(cumulative * 100) / 100,
      pnl: Math.round(t.pnl * 100) / 100,
    };
  });
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    value?: number;
    payload?: DataPoint;
  }>;
  label?: string;
}

const CustomTooltip = ({ active, payload, label }: CustomTooltipProps) => {
  if (!active || !payload?.length) return null;

  const cumulative = payload[0]?.value ?? 0;
  const pnl = (payload[0]?.payload as DataPoint)?.pnl ?? 0;

  return (
    <div className="bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-xs space-y-1">
      <p className="text-zinc-400">{label}</p>
      <div className="flex justify-between gap-4">
        <span className="text-zinc-500">Equity</span>
        <span
          className={`font-mono font-medium ${cumulative >= 0 ? "text-emerald-400" : "text-red-400"}`}
        >
          {cumulative >= 0 ? "+" : ""}${cumulative.toFixed(2)}
        </span>
      </div>
      <div className="flex justify-between gap-4">
        <span className="text-zinc-500">Trade PnL</span>
        <span
          className={`font-mono font-medium ${pnl >= 0 ? "text-emerald-400" : "text-red-400"}`}
        >
          {pnl >= 0 ? "+" : ""}${pnl.toFixed(2)}
        </span>
      </div>
    </div>
  );
};

interface Props {
  trades: Trade[];
}

export function PnLChart({ trades }: Props) {
  const data = buildEquityCurve(trades);

  if (data.length === 0) {
    return (
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
        <h2 className="text-white font-medium mb-3">Equity Curve</h2>
        <div className="h-48 flex items-center justify-center">
          <p className="text-zinc-600 text-sm">Belum ada trade yang closed.</p>
        </div>
      </div>
    );
  }

  const lastValue = data[data.length - 1]?.cumulative ?? 0;

  // Fix #1 — warna ditentukan per data point, bukan hanya dari lastValue
  // Pakai dua gradient terpisah dan dua Area — satu untuk positif, satu negatif
  const hasPositive = data.some((d) => d.cumulative >= 0);
  const hasNegative = data.some((d) => d.cumulative < 0);

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-white font-medium">Equity Curve</h2>
        <div className="flex items-center gap-3 text-xs">
          {hasPositive && (
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              <span className="text-zinc-500">Profit</span>
            </span>
          )}
          {hasNegative && (
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-red-500" />
              <span className="text-zinc-500">Loss</span>
            </span>
          )}
          <span
            className={`font-mono font-semibold ${lastValue >= 0 ? "text-emerald-400" : "text-red-400"}`}
          >
            {lastValue >= 0 ? "+" : ""}${lastValue.toFixed(2)}
          </span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={200}>
        <AreaChart
          data={data}
          margin={{ top: 4, right: 4, bottom: 0, left: 4 }}
        >
          <defs>
            {/* Fix #1 — gradient hijau untuk area positif */}
            <linearGradient id="gradientPositive" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#10b981" stopOpacity={0.02} />
            </linearGradient>
            {/* Fix #1 — gradient merah untuk area negatif */}
            <linearGradient id="gradientNegative" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ef4444" stopOpacity={0.02} />
              <stop offset="95%" stopColor="#ef4444" stopOpacity={0.3} />
            </linearGradient>
          </defs>

          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
          <XAxis
            dataKey="label"
            tick={{ fill: "#52525b", fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            // Tampilkan setiap N tick agar tidak crowded
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fill: "#52525b", fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v) => `$${v}`}
          />

          {/* Garis referensi di y=0 */}
          <ReferenceLine y={0} stroke="#52525b" strokeDasharray="3 3" />

          <Tooltip content={<CustomTooltip />} />

          {/* Area positif (di atas 0) */}
          <Area
            type="monotone"
            dataKey="cumulative"
            stroke="#10b981"
            strokeWidth={2}
            fill="url(#gradientPositive)"
            dot={false}
            activeDot={{ r: 4, fill: "#10b981", strokeWidth: 0 }}
            // Hanya tampil di atas 0
            baseValue={0}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
