import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getMLStatus, trainModel } from "../api/bot";

export function Settings() {
  const queryClient = useQueryClient();
  const [trainLimit, setTrainLimit] = useState(1000);
  const [trainTF, setTrainTF] = useState("1h");
  const [trainLog, setTrainLog] = useState<string | null>(null);

  const { data: mlStatus } = useQuery({
    queryKey: ["mlStatus"],
    queryFn: getMLStatus,
  });

  const trainMutation = useMutation({
    mutationFn: () => trainModel(trainLimit, trainTF),
    onSuccess: (result) => {
      setTrainLog(
        `✅ Training selesai!\n` +
          `Samples: ${result.total_samples}\n` +
          `Accuracy: ${(result.mean_accuracy * 100).toFixed(2)}%\n` +
          `Fold scores: ${result.fold_scores.map((s: number) => (s * 100).toFixed(1) + "%").join(", ")}\n` +
          `Top features: ${result.top_features.map(([f]: [string]) => f).join(", ")}`,
      );
      queryClient.invalidateQueries({ queryKey: ["mlStatus"] });
    },
    onError: (err: Error) => {
      setTrainLog(`❌ Error: ${err.message}`);
    },
  });

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
        <h1 className="text-xl font-semibold">Settings</h1>

        {/* Model status */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-white font-medium">AI Model</h2>
            <span
              className={`text-xs px-2 py-1 rounded-full font-medium ${
                mlStatus?.model_exists
                  ? "bg-emerald-500/20 text-emerald-400"
                  : "bg-zinc-700 text-zinc-400"
              }`}
            >
              {mlStatus?.model_exists ? "✓ Model ready" : "✗ Not trained"}
            </span>
          </div>

          <p className="text-zinc-500 text-sm">
            {mlStatus?.message ?? "Checking model status..."}
          </p>

          {/* Train controls */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-zinc-500 text-xs block mb-1">
                Candle limit
              </label>
              <select
                value={trainLimit}
                onChange={(e) => setTrainLimit(Number(e.target.value))}
                className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-white"
              >
                {[500, 1000, 2000].map((v) => (
                  <option key={v} value={v}>
                    {v} candles
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-zinc-500 text-xs block mb-1">
                Timeframe
              </label>
              <select
                value={trainTF}
                onChange={(e) => setTrainTF(e.target.value)}
                className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-white"
              >
                {["1h", "4h", "1d"].map((tf) => (
                  <option key={tf} value={tf}>
                    {tf}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <button
            onClick={() => {
              setTrainLog(null);
              trainMutation.mutate();
            }}
            disabled={trainMutation.isPending}
            className="w-full py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500
                       disabled:opacity-50 disabled:cursor-not-allowed
                       text-white text-sm font-medium transition-colors"
          >
            {trainMutation.isPending
              ? "⏳ Training... (1-2 menit)"
              : "🧠 Train Model"}
          </button>

          {/* Training log */}
          {trainLog && (
            <pre
              className="bg-zinc-950 border border-zinc-800 rounded-lg p-3
                            text-xs text-zinc-300 font-mono whitespace-pre-wrap"
            >
              {trainLog}
            </pre>
          )}
        </div>

        {/* Info box */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 space-y-3">
          <h2 className="text-white font-medium">Bot Configuration</h2>
          <p className="text-zinc-500 text-sm">
            Konfigurasi symbol, timeframe, dan risk parameter dilakukan melalui
            file <code className="text-indigo-400">.env</code> di folder
            backend.
          </p>
          <div className="bg-zinc-950 rounded-lg p-3 font-mono text-xs space-y-1">
            {[
              ["SYMBOL", "BTC/USDT"],
              ["TIMEFRAME", "1h"],
              ["MAX_RISK_PER_TRADE", "0.02 (2%)"],
              ["STOP_LOSS_PCT", "0.03 (3%)"],
              ["INITIAL_CAPITAL", "10000.0"],
            ].map(([key, val]) => (
              <div key={key} className="flex gap-3">
                <span className="text-zinc-500 w-36">{key}</span>
                <span className="text-emerald-400">{val}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Danger zone */}
        <div className="bg-zinc-900 border border-red-900/40 rounded-xl p-5 space-y-3">
          <h2 className="text-red-400 font-medium">Danger Zone</h2>
          <p className="text-zinc-500 text-sm">
            Pastikan bot dalam kondisi stopped sebelum melakukan live trading.
            Selalu gunakan paper trading minimal 2-4 minggu sebelum live.
          </p>
          <div className="text-xs text-zinc-600 space-y-1">
            <p>• Sharpe Ratio harus &gt; 1.0 di paper trading</p>
            <p>• Max Drawdown harus &lt; 15%</p>
            <p>• Win rate harus &gt; 45% selama minimal 50 trades</p>
          </div>
        </div>
      </div>
    </div>
  );
}
