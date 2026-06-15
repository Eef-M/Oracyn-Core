import { useBotControl } from "../hooks/useBotControl";

export function BotControls() {
  const { isRunning, isPaper, capital, isStarting, isStopping, start, stop } =
    useBotControl();

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-white font-medium">Bot Control</h2>
        <span
          className={`text-xs px-2 py-1 rounded-full font-medium ${
            isRunning
              ? "bg-emerald-500/20 text-emerald-400"
              : "bg-zinc-700 text-zinc-400"
          }`}
        >
          {isRunning ? "● Running" : "○ Stopped"}
        </span>
      </div>

      {/* Mode indicator */}
      <div className="flex items-center gap-2 text-sm">
        <span className="text-zinc-500">Mode:</span>
        <span
          className={`font-medium ${isPaper ? "text-amber-400" : "text-emerald-400"}`}
        >
          {isPaper ? "📋 Paper Trading" : "💰 Live Trading"}
        </span>
      </div>

      {/* Capital */}
      <div className="flex items-center gap-2 text-sm">
        <span className="text-zinc-500">Capital:</span>
        <span className="text-white font-mono">
          ${capital.toLocaleString("en-US", { minimumFractionDigits: 2 })}
        </span>
      </div>

      {/* Buttons */}
      <div className="flex gap-2 pt-1">
        {!isRunning ? (
          <>
            {/* Paper trading */}
            <button
              onClick={() => start(true)}
              disabled={isStarting}
              className="flex-1 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 
                         disabled:opacity-50 disabled:cursor-not-allowed
                         text-white text-sm font-medium transition-colors"
            >
              {isStarting ? "Starting..." : "▶ Start Paper"}
            </button>

            {/* Live trading — Need Confirmation */}
            <button
              onClick={() => {
                if (
                  confirm(
                    "⚠️ Live trading uses real money! Are you sure you want to continue?",
                  )
                ) {
                  start(false);
                }
              }}
              disabled={isStarting}
              className="px-3 py-2 rounded-lg border border-red-800 hover:bg-red-900/30
                         disabled:opacity-50 disabled:cursor-not-allowed
                         text-red-400 text-sm font-medium transition-colors"
            >
              Live
            </button>
          </>
        ) : (
          <button
            onClick={stop}
            disabled={isStopping}
            className="flex-1 py-2 rounded-lg bg-red-700 hover:bg-red-600
                       disabled:opacity-50 disabled:cursor-not-allowed
                       text-white text-sm font-medium transition-colors"
          >
            {isStopping ? "Stopping..." : "■ Stop Bot"}
          </button>
        )}
      </div>
    </div>
  );
}
